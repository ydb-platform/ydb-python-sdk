"""Check actual chaos completion, native observations and acknowledged data."""

import json
import math
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

SCENARIOS = [
    "01-switchover",
    "02-takedown-synchronized",
    "03-takedown-primary",
    "04-failover-synchronized",
    "05-failover-primary",
]


def command(*args, check=True):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check).stdout


def main():
    artifacts = Path("bridge-artifacts")
    artifacts.mkdir(exist_ok=True)
    result = {"errors": [], "action_outcome": os.environ.get("ACTION_OUTCOME")}
    for name in ("ydb-workload-current", "ydb-bridge-probe", "ydb-chaos-monkey"):
        (artifacts / f"{name}.log").write_text(command("docker", "logs", name, check=False))
    try:
        if result["action_outcome"] != "success":
            result["errors"].append("Action did not complete successfully")
        chaos = json.loads(command("docker", "inspect", "ydb-chaos-monkey"))[0]["State"]
        result["chaos"] = chaos
        log = (artifacts / "ydb-chaos-monkey.log").read_text()
        if chaos["Status"] != "exited" or chaos["ExitCode"] != 0 or "Chaos Monkey finished" not in log:
            result["errors"].append("Chaos sequence did not finish successfully during the workload")
        for scenario in SCENARIOS:
            if f"Running scenario: {scenario}" not in log:
                result["errors"].append(f"Scenario not executed: {scenario}")
        probe_state = json.loads(command("docker", "inspect", "ydb-bridge-probe"))[0]["State"]
        if probe_state["Running"]:
            command("docker", "exec", "ydb-bridge-probe", "touch", "/tmp/bridge-probe-stop")
        command("docker", "wait", "ydb-bridge-probe")
        command("docker", "cp", "ydb-bridge-probe:/tmp/bridge-probe.json", str(artifacts / "probe.json"))
        result["probe"] = json.loads((artifacts / "probe.json").read_text())
        if not result["probe"].get("passed"):
            result["errors"].append("Independent data probe failed")
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
            count = metric(f'sum(sdk_operations_success_total{{ref="current",operation_type="{operation}"}})')
            observations[operation] = count
            if not math.isfinite(count) or count <= 0:
                result["errors"].append(f"No successful native {operation} observations")
        observations["errors"] = metric('sum(sdk_operations_failure_total{ref="current"})')
        if observations["errors"]:
            result["errors"].append("Native workload reported final operation failures")
        result["native_observations"] = observations
        nodes = json.loads(
            command(
                "docker",
                "inspect",
                "ydb-storage-1",
                "ydb-storage-2",
                "ydb-database-1",
                "ydb-database-2",
            )
        )
        result["node_states"] = {node["Name"]: node["State"] for node in nodes}
        result["node_restarts"] = {node["Name"]: node["RestartCount"] for node in nodes}
        if any(node["State"]["OOMKilled"] or node["RestartCount"] for node in nodes):
            result["errors"].append("YDB node was OOM killed or unexpectedly restarted")
    except Exception as error:
        result["errors"].append(repr(error))
    result["passed"] = not result["errors"]
    (artifacts / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
