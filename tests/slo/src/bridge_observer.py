"""Read the server's discovery RPC directly, independently of driver balancing."""

import grpc
import ydb
from ydb import _apis


class BridgeObserver:
    def __init__(self, endpoints, database):
        self.database = database
        self.channels = [grpc.insecure_channel(endpoint) for endpoint in endpoints]
        self.stubs = [_apis.DiscoveryService.Stub(channel) for channel in self.channels]

    def snapshot(self):
        for stub in self.stubs:
            try:
                response = stub.ListEndpoints(
                    _apis.ydb_discovery.ListEndpointsRequest(database=self.database), timeout=2
                )
                if response.operation.status != ydb.StatusCode.SUCCESS:
                    continue
                result = _apis.ydb_discovery.ListEndpointsResult()
                if not response.operation.result.Unpack(result):
                    continue
                states = {pile.pile_name: pile.state for pile in result.pile_states}
                primary = next((name for name, state in states.items() if state == 1), None)
                return {
                    "states": states,
                    "primary": primary,
                    "node_piles": {str(ep.node_id): ep.bridge_pile_name for ep in result.endpoints if not ep.ssl},
                }
            except grpc.RpcError:
                continue
        return None

    def close(self):
        for channel in self.channels:
            channel.close()


def route_observation(node_id, before, after):
    before, after = before or {}, after or {}
    key = str(node_id)
    pile = after.get("node_piles", {}).get(key)
    stable = bool(
        before.get("primary")
        and before.get("primary") == after.get("primary")
        and before.get("states") == after.get("states")
        and pile
        and before.get("node_piles", {}).get(key) == pile
    )
    return {
        "node_id": node_id,
        "pile": pile,
        "primary": after.get("primary"),
        "stable": stable,
        "both_piles_visible": {"pile-1", "pile-2"} <= set(after.get("node_piles", {}).values()),
        "fallback": stable and after["states"].get(pile) == 3 and pile != after["primary"],
        "before": before,
        "after": after,
    }
