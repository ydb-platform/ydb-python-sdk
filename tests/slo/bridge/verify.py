"""Verify completion and recovery of the GitHub-hosted Bridge workload."""

import json
import math
import os
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

SCENARIOS = (
    "01-switchover",
    "02-takedown-synchronized",
    "03-takedown-primary",
    "04-failover-synchronized",
    "05-failover-primary",
)


def command(*args, check=True, timeout=90, stderr=subprocess.STDOUT):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=stderr, check=check, timeout=timeout).stdout


def check_chaos(log, state, restarts):
    errors = []
    if state["Status"] != "exited" or state["ExitCode"] != 0 or restarts or "Chaos Monkey finished" not in log:
        errors.append("Chaos sequence did not finish without a process restart")
    for scenario in SCENARIOS:
        if f"Running scenario: {scenario}" not in log:
            errors.append(f"Scenario not executed: {scenario}")
    if log.count("] Recovered: ") != len(SCENARIOS):
        errors.append("Expected five completed chaos recoveries")
    return errors


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
        result["errors"].extend(check_chaos(log, chaos, chaos_info["RestartCount"]))
        result["completed_scenarios"] = len(SCENARIOS) if not result["errors"] else None
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
            )
        )
        result["container_states"] = {
            node["Name"]: {"state": node["State"], "restarts": node["RestartCount"]} for node in containers
        }
        if any(node["State"]["OOMKilled"] or node["RestartCount"] for node in containers):
            result["errors"].append("A container was OOM killed or unexpectedly restarted")
        for node in containers:
            if node["Name"] == "/ydb-workload-current" and (
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
