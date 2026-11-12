"""Configure a pinned Action checkout for a bounded GitHub-hosted run."""

import argparse
import copy
import json
import subprocess
import shutil
from pathlib import Path


def prepare(action, image):
    deploy = action.resolve() / "deploy"
    compose = deploy / "compose.bridge.yml"
    rendered = subprocess.check_output(
        [
            "docker",
            "compose",
            "-f",
            str(compose),
            "config",
            "--no-interpolate",
            "--format",
            "json",
        ],
        text=True,
    )
    config = json.loads(rendered)
    for service in config["services"].values():
        if "build" in service and service["build"]["context"].endswith("/ydb"):
            service["build"].setdefault("args", {})["YDB_IMAGE"] = image
            service["mem_limit"] = "2g"
    for name in ("workload-current", "workload-baseline"):
        config["services"][name]["deploy"]["resources"]["reservations"]["memory"] = "256m"
        service = config["services"][name]
        hosts = service.get("extra_hosts", [])
        if isinstance(hosts, dict):
            hosts = [
                f"{host}:{address}"
                for host, addresses in hosts.items()
                for address in (addresses if isinstance(addresses, list) else [addresses])
            ]
        service["extra_hosts"] = [host for host in hosts if not host.startswith(("ydb:", "ydb="))] + [
            "ydb:172.28.0.11",
            "ydb:172.28.0.12",
        ]
    for filename in ("config.yaml", "config.bridge.yaml"):
        path = deploy / "ydb/rootfs/opt/ydb.tech/ydbd/cfg" / filename
        text = path.read_text()
        if text.count("cpu_count: 4") != 1 or text.count("hard_limit_bytes: 17179869184") != 1:
            raise RuntimeError(f"Unexpected resource configuration: {path}")
        path.write_text(
            text.replace("cpu_count: 4", "cpu_count: 1").replace(
                "hard_limit_bytes: 17179869184", "hard_limit_bytes: 1610612736"
            )
        )
    readiness = deploy / "ydb/rootfs/opt/ydb.tech/scripts/ydbd/check-readiness.sh"
    text = readiness.read_text()
    if text.count("local max_attempts=30") != 2:
        raise RuntimeError("Unexpected readiness implementation")
    readiness.write_text(text.replace("local max_attempts=30", "local max_attempts=150", 1))
    scenario = deploy / "chaos/rootfs/opt/ydb.tech/chaos/bridge-scenarios/01-switchover.sh"
    shutil.copyfile(Path(__file__).with_name("switchover.sh"), scenario)
    scenario.chmod(0o755)
    probe = copy.deepcopy(config["services"]["workload-current"])
    probe.update(
        container_name="ydb-bridge-probe", entrypoint=["python", "/src/tests/slo/src/primary_probe.py"], command=[]
    )
    probe.pop("deploy", None)
    probe["mem_limit"] = "768m"
    probe["restart"] = "no"
    environment = probe.get("environment", {})
    if isinstance(environment, list):
        environment = {item.partition("=")[0]: item.partition("=")[2] if "=" in item else None for item in environment}
    probe["environment"] = {**environment, "ORACLE_ENDPOINTS": "ydb-storage-1:2136,ydb-storage-2:2136"}
    config["services"]["bridge-probe"] = probe
    compose.write_text(json.dumps(config, indent=2) + "\n")
    subprocess.run(["docker", "compose", "-f", str(compose), "config", "--quiet"], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", type=Path)
    parser.add_argument("image")
    args = parser.parse_args()
    prepare(args.action, args.image)
