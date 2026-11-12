"""Verify live role-aware routing, recovery and independently audited data."""

import json
import math
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request

from checks import MODES, audit_rows, check_node_events, check_routing

SCENARIOS = (
    "01-switchover",
    "02-takedown-synchronized",
    "03-takedown-primary",
    "04-failover-synchronized",
    "05-failover-primary",
)


def command(*args, check=True, timeout=90):
    return subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check, timeout=timeout
    ).stdout


def json_lines(text):
    rows = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except json.JSONDecodeError:
            continue
    return rows


def main():
    artifacts = Path("bridge-artifacts")
    artifacts.mkdir(exist_ok=True)
    result = {"errors": [], "action_outcome": os.environ.get("ACTION_OUTCOME")}
    for name in ("ydb-workload-current", "ydb-chaos-monkey"):
        (artifacts / f"{name}.log").write_text(command("docker", "logs", name, check=False))
    try:
        (artifacts / "healthcheck.json").write_text(
            command(
                "docker",
                "exec",
                "ydb-storage-1",
                "/opt/ydb.tech/ydb/bin/ydb",
                "-e",
                "grpc://localhost:2136",
                "monitoring",
                "healthcheck",
                "--format",
                "json",
                check=False,
                timeout=30,
            )
        )
    except Exception as error:
        (artifacts / "healthcheck-error.txt").write_text(repr(error))
    try:
        if result["action_outcome"] != "success":
            result["errors"].append("Action did not complete successfully")
        chaos_info = json.loads(command("docker", "inspect", "ydb-chaos-monkey"))[0]
        chaos = chaos_info["State"]
        log = (artifacts / "ydb-chaos-monkey.log").read_text()
        if (
            chaos["Status"] != "exited"
            or chaos["ExitCode"] != 0
            or chaos_info["RestartCount"]
            or "Chaos Monkey finished" not in log
        ):
            result["errors"].append("Chaos sequence did not finish without a process restart")
        for scenario in SCENARIOS:
            if f"Running scenario: {scenario}" not in log:
                result["errors"].append(f"Scenario not executed: {scenario}")
        state = json.loads(command("docker", "inspect", "ydb-bridge-probe"))[0]
        if state["State"]["Running"]:
            command("docker", "exec", "ydb-bridge-probe", "touch", "/tmp/bridge-probe-stop")
        command("docker", "wait", "ydb-bridge-probe", timeout=150)
        probe_log = command("docker", "logs", "ydb-bridge-probe", check=False)
        (artifacts / "ydb-bridge-probe.log").write_text(probe_log)
        command("docker", "cp", "ydb-bridge-probe:/tmp/bridge-probe.json", str(artifacts / "probe.json"))
        probe = json.loads((artifacts / "probe.json").read_text())
        result["probe"] = probe
        if not probe.get("passed") or state["RestartCount"]:
            result["errors"].append("Probe failed or its process was restarted")
        events = json_lines(probe_log)
        for mode in (*MODES, "control-table"):
            if sum(row.get("event") == "driver_started" and row.get("mode") == mode for row in events) != 1:
                result["errors"].append(f"Expected one long-lived driver for {mode}")
        routing, errors = check_routing(log, events, probe["stopped_at"])
        result["routing"] = routing
        result["errors"].extend(errors)
        result["errors"].extend(check_node_events(log, json_lines((artifacts / "docker-events.jsonl").read_text())))
        if not re.fullmatch(r"primary_probe_[a-f0-9]+", probe["table"]):
            raise ValueError("Unexpected audit table name")
        output = command(
            "docker",
            "exec",
            "ydb-database-1",
            "/opt/ydb.tech/ydb/bin/ydb",
            "-e",
            "grpc://localhost:2136",
            "-d",
            "/Root/testdb",
            "--no-discovery",
            "sql",
            "-s",
            f"SELECT `mode`, seq, payload FROM `{probe['table']}`;",
            "--format",
            "json-unicode",
        )
        (artifacts / "audit-rows.jsonl").write_text(output)
        missing = audit_rows(probe, json_lines(output))
        (artifacts / "missing.json").write_text(json.dumps(missing, indent=2))
        result["audit"] = {
            "confirmed": sum(len(item["confirmed"]) for item in probe["modes"].values()),
            "missing": len(missing),
        }
        if missing:
            result["errors"].append("Acknowledged probe rows were lost or corrupted")
        ip = command(
            "docker",
            "inspect",
            "--format",
            "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
            "ydb-prometheus",
        ).strip()

        def metric(expression):
            url = f"http://{ip}:9090/api/v1/query?" + urllib.parse.urlencode({"query": expression})
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.load(response)
            if data["status"] != "success":
                raise RuntimeError(data)
            return sum(float(item["value"][1]) for item in data["data"]["result"])

        observations = {}
        for operation in ("read", "write"):
            selector = f'sdk_operations_success_total{{ref="current",operation_type="{operation}"}}'
            count, recent = metric(f"sum({selector})"), metric(f"sum(increase({selector}[120s]))")
            observations[operation], observations[f"recent_{operation}"] = count, recent
            if not math.isfinite(count) or not math.isfinite(recent) or count <= 0 or recent <= 0:
                result["errors"].append(f"No recent successful native {operation} observations")
        observations["errors"] = metric('sum(sdk_operations_failure_total{ref="current"})')
        result["native_observations"] = observations
        containers = json.loads(
            command(
                "docker",
                "inspect",
                "ydb-storage-1",
                "ydb-storage-2",
                "ydb-database-1",
                "ydb-database-2",
                "ydb-workload-current",
                "ydb-bridge-probe",
            )
        )
        result["container_states"] = {
            node["Name"]: {"state": node["State"], "restarts": node["RestartCount"]} for node in containers
        }
        if any(node["State"]["OOMKilled"] or node["RestartCount"] for node in containers):
            result["errors"].append("A container was OOM killed or unexpectedly restarted")
        for node in containers:
            if node["Name"] in ("/ydb-workload-current", "/ydb-bridge-probe") and (
                node["State"]["Status"] != "exited" or node["State"]["ExitCode"] != 0
            ):
                result["errors"].append(f"Workload process did not exit successfully: {node['Name']}")
    except Exception as error:
        result["errors"].append(repr(error))
    result["passed"] = not result["errors"]
    (artifacts / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
