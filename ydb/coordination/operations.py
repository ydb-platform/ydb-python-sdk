from ydb import operation as ydb_op
from ydb import _apis

class DescribeNodeOperation(ydb_op.Operation):
    def __init__(self, rpc_state, response, driver=None):
        super().__init__(rpc_state, response, driver)

        self.status = response.operation.status

        result = _apis.ydb_coordination.DescribeNodeResult()
        response.operation.result.Unpack(result)

        node_info = result.self
        self.path = node_info.name
        self.node_owner = node_info.owner
        self.effective_permissions = node_info.effective_permissions
        self.config = result.config

        if self.config:
            self.session_grace_period_millis = self.config.session_grace_period_millis
            self.attach_consistency_mode = self.config.attach_consistency_mode
            self.read_consistency_mode = self.config.read_consistency_mode
        else:
            self.session_grace_period_millis = None
            self.attach_consistency_mode = None
            self.read_consistency_mode = None

    def __repr__(self):
        return f"DescribeNodeOperation<id={self.id}, path={self.path}, status={self.status}>"

    __str__ = __repr__


class CreateNodeOperation(ydb_op.Operation):
    def __init__(self, rpc_state, response, path, driver=None):
        super().__init__(rpc_state, response, driver)
        self.path = path
        self.status = response.operation.status

    def __repr__(self):
        return f"CreateNodeOperation<id={self.id}, path={self.path}, status={self.status}>"

class DropNodeOperation(ydb_op.Operation):
    def __init__(self, rpc_state, response, path, driver=None):
        super().__init__(rpc_state, response, driver)
        self.path = path
        self.status = response.operation.status

    def __repr__(self):
        return f"DropNodeOperation<id={self.id}, path={self.path}, status={self.status}>"
