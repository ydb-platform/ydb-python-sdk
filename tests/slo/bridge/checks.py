"""Acceptance checks for independently observed live Bridge routing and data."""

from datetime import datetime
import re

MODES = ("sync-table", "sync-query", "async-table", "async-query")


def stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def check_routing(log, events, stopped_at):
    errors, windows, beginnings = [], [], {}
    pattern = r"\[([^\]]+)\] PRIMARY_WINDOW_(BEGIN|END) (\w+) (\S+)"
    for when, kind, name, pile in re.findall(pattern, log):
        if kind == "BEGIN":
            beginnings[name] = (stamp(when), pile)
        elif name in beginnings:
            start, initial_pile = beginnings.pop(name)
            windows.append({"name": name, "start": start, "end": stamp(when), "pile": pile})
            if pile != initial_pile or stamp(when) - start < 150:
                errors.append(f"Invalid PRIMARY observation window: {name}")
    if [w["name"] for w in windows] != ["initial", "switched", "restored"] or beginnings:
        errors.append("Missing the three controlled PRIMARY observation windows")
    elif not (windows[0]["pile"] == windows[2]["pile"] != windows[1]["pile"]):
        errors.append("PRIMARY did not switch to the other pile and back")
    details = {"primary_windows": [], "recovery_windows": [], "fallback": {}}
    for window in windows:
        end, primary = window["end"], window["pile"]
        late = [row for row in events if end - 30 <= row.get("ts", 0) <= end]
        routes = [
            row
            for row in late
            if row.get("event") == "session_created"
            and row.get("stable")
            and row.get("both_piles_visible")
            and row.get("primary") == primary
        ]
        observation = {**window, "modes": {}}
        for mode in MODES:
            samples = [row for row in routes if row.get("mode") == mode]
            writes = sum(row.get("event") == "operation" and row.get("ok") and row.get("mode") == mode for row in late)
            wrong = [row for row in samples if row.get("pile") != primary]
            observation["modes"][mode] = {"sessions": len(samples), "wrong_pile": len(wrong), "writes": writes}
            if len(samples) < 3 or writes < 3 or wrong:
                errors.append(f"PRIMARY routing or data progress failed for {mode} in {window['name']}")
        control = {row.get("pile") for row in routes if row.get("mode") == "control-table"}
        observation["control_piles"] = sorted(pile for pile in control if pile)
        if control != {"pile-1", "pile-2"}:
            errors.append(f"Disabled-option control did not use both piles in {window['name']}")
        details["primary_windows"].append(observation)
    fallback = re.findall(r"\[([^\]]+)\] PRIMARY_FALLBACK_(BEGIN|END) (\S+)", log)
    if len(fallback) != 2 or [item[1] for item in fallback] != ["BEGIN", "END"] or fallback[0][2] != fallback[1][2]:
        errors.append("Missing controlled primary-compute outage")
    else:
        start, end = stamp(fallback[0][0]), stamp(fallback[1][0])
        for mode in MODES:
            count = sum(
                row.get("event") == "session_created"
                and row.get("mode") == mode
                and start + 2 <= row.get("ts", 0) <= end
                and row.get("stable")
                and row.get("fallback")
                and row.get("primary") == fallback[0][2]
                for row in events
            )
            details["fallback"][mode] = count
            if not count:
                errors.append(f"No synchronized fallback observed for {mode} while PRIMARY compute was stopped")
    recoveries = re.findall(r"\[([^\]]+)\] Recovered: ([^\n]+)", log)
    if len(recoveries) != 5:
        errors.append(f"Expected five completed chaos recoveries, found {len(recoveries)}")
    for when, name in recoveries:
        start = stamp(when)
        counts = {
            mode: sum(
                row.get("event") == "operation"
                and row.get("ok")
                and row.get("mode") == mode
                and start <= row.get("ts", 0) <= start + 90
                for row in events
            )
            for mode in MODES
        }
        details["recovery_windows"].append({"name": name, "writes": counts})
        if any(count < 3 for count in counts.values()):
            errors.append(f"Some probe modes did not recover after {name}")
    details["final_writes"] = {
        mode: sum(
            row.get("event") == "operation"
            and row.get("ok")
            and row.get("mode") == mode
            and stopped_at - 60 <= row.get("ts", 0) <= stopped_at
            for row in events
        )
        for mode in MODES
    }
    if any(count < 3 for count in details["final_writes"].values()):
        errors.append("Some probe modes stopped making progress at the end of the run")
    details["final_routing"] = {}
    if windows:
        primary = windows[0]["pile"]
        for mode in MODES:
            samples = [
                row
                for row in events
                if row.get("event") == "session_created"
                and row.get("mode") == mode
                and stopped_at - 30 <= row.get("ts", 0) <= stopped_at
                and row.get("stable")
                and row.get("both_piles_visible")
                and row.get("primary") == primary
            ]
            wrong = sum(row.get("pile") != primary for row in samples)
            details["final_routing"][mode] = {"sessions": len(samples), "wrong_pile": wrong}
            if len(samples) < 3 or wrong:
                errors.append(f"PRIMARY routing did not recover at the end for {mode}")
    return details, errors


def audit_rows(probe, rows):
    stored = {(row["mode"], int(row["seq"])): row["payload"] for row in rows}
    return [
        {"mode": mode, "seq": seq}
        for mode, result in probe["modes"].items()
        for seq in result["confirmed"]
        if stored.get((mode, seq)) != f"{probe['table']}:{mode}:{seq}"
    ]


def check_node_events(log, events):
    windows = re.findall(r"\[([^\]]+)\] PRIMARY_WINDOW_(BEGIN|END) (\w+) (\S+)", log)
    if len(windows) != 6:
        return ["Missing node-event observation boundaries"]
    first, last = stamp(windows[0][0]), stamp(windows[-1][0])
    errors = []
    for event in events:
        when = event["timeNano"] / 1e9 if event.get("timeNano") else event["time"]
        if first <= when <= last:
            errors.append("A database process changed during the role-only observation windows")
            break
    fallback = re.findall(r"\[([^\]]+)\] PRIMARY_FALLBACK_(BEGIN|END) (\S+)", log)
    if len(fallback) != 2:
        return errors + ["Missing controlled outage node boundaries"]
    start, end, pile = stamp(fallback[0][0]), stamp(fallback[1][0]), fallback[0][2]
    stops = [
        event
        for event in events
        if (event.get("Action") or event.get("status")) == "stop"
        and event.get("Actor", {}).get("Attributes", {}).get("ydb.node.location.pile") == pile
        and start <= (event["timeNano"] / 1e9 if event.get("timeNano") else event["time"]) <= end
    ]
    if not stops:
        errors.append("No Docker evidence that PRIMARY compute actually stopped")
    return errors
