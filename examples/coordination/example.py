import time
import threading
import ydb

NODE_PATH = "/local/node_name1"
SEMAPHORE_NAME = "semaphore"


def linear_workload(client, text):
    session = client.session(NODE_PATH)
    semaphore = session.semaphore(SEMAPHORE_NAME)
    for i in range(3):
        semaphore.acquire()
        for j in range(3):
            print(f"{text} iteration {i}-{j}")
            time.sleep(0.1)
        semaphore.release()
        time.sleep(0.05)
    session.close()


def context_manager_workload(client, text):
    with client.session(NODE_PATH) as session:
        for i in range(3):
            with session.semaphore(SEMAPHORE_NAME):
                for j in range(3):
                    print(f"{text} iteration {i}-{j}")
                    time.sleep(0.1)
            time.sleep(0.05)


def run(endpoint, database):
    with ydb.Driver(
        endpoint=endpoint,
        database=database,
        credentials=ydb.credentials_from_env_variables(),
        root_certificates=ydb.load_ydb_root_certificate(),
    ) as driver:
        driver.wait(timeout=5, fail_fast=True)

        driver.coordination_client.create_node(NODE_PATH)

        threads = []

        for i in range(4):
            worker_name = f"worker {i+1}"
            if i < 2:
                thread = threading.Thread(target=linear_workload, args=(driver.coordination_client, worker_name))
            else:
                thread = threading.Thread(
                    target=context_manager_workload, args=(driver.coordination_client, worker_name)
                )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
