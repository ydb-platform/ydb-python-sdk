import pytest
import ydb
from ydb.coordination.client import CoordinationClient
import time



@pytest.mark.integration
def test_coordination_client_local():
    driver_config = ydb.DriverConfig(
        endpoint="grpc://localhost:2136",
        database="/local",
    )

    with ydb.Driver(driver_config) as driver:
        for _ in range(10):
            try:
                driver.wait(timeout=5)
                break
            except Exception:
                time.sleep(1)


        scheme = ydb.SchemeClient(driver)
        base_path = "/local/coordination"

        try:
            scheme.describe_path(base_path)
        except ydb.issues.SchemeError:
            scheme.make_directory(base_path)
            desc = scheme.describe_path(base_path)
            assert desc is not None, f"Directory {base_path} was not created"


        node_path = f"{base_path}/test_node"

        client = CoordinationClient(driver)


        create_future = client.create_node(path=node_path)
        assert create_future is not None


        res_desc = client.describe_node(path=node_path)
        assert res_desc is not None


        res_delete = client.delete_node(path=node_path)
        assert res_delete is not None

@pytest.mark.integration
def test_coordination_lock_lifecycle():
    driver_config = ydb.DriverConfig(
        endpoint="grpc://localhost:2136",
        database="/local",
    )

    with ydb.Driver(driver_config) as driver:
        for _ in range(10):
            try:
                driver.wait(timeout=5)
                break
            except Exception:
                time.sleep(1)

        scheme = driver.scheme_client
        base_path = "/local/coordination"
        try:
            scheme.describe_path(base_path)
        except ydb.SchemeError:
            scheme.make_directory(base_path)
            desc = scheme.describe_path(base_path)
            assert desc is not None, f"Directory {base_path} was not created"

        # создаём client
        client = CoordinationClient(driver)

        lock_path = f"{base_path}/test_lock"


        with client.lock(lock_path, timeout=2000, count=1) as lock:
            assert lock._session_id is not None, "Lock должен иметь session_id после acquire"


            sem_state = client.describe_node(lock_path)
            assert sem_state is not None, "Семафор должен существовать после acquire"


        assert lock._session_id is None, "Lock должен быть освобождён после выхода из with"


        sem_state_after = client.describe_node(lock_path)
        assert sem_state_after is not None, "Семафор всё ещё существует"