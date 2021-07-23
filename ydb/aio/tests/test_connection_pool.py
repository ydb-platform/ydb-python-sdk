import asyncio

from ydb.aio.driver import Driver
import pytest
import ydb

from concurrent.futures import ProcessPoolExecutor


@pytest.mark.asyncio
async def test_async_call(endpoint, database):
    driver_config = ydb.DriverConfig(
        endpoint, database, credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    driver = Driver(driver_config=driver_config)

    await driver.scheme_client.make_directory("/local/lol")


@pytest.mark.asyncio
async def test_disconnect_by_call(endpoint, database, docker_project):
    driver_config = ydb.DriverConfig(
        endpoint, database, credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    driver = Driver(driver_config=driver_config)

    await driver.wait(timeout=10)

    docker_project.restart()

    try:
        await driver.scheme_client.make_directory("/local/lol")
    except Exception as e:
        pass
    await asyncio.sleep(5)
    assert len(driver._store.connections) == 0


@pytest.mark.asyncio
async def test_session(endpoint, database):
    driver_config = ydb.DriverConfig(
        endpoint, database, credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    driver = Driver(driver_config=driver_config)

    await driver.wait(timeout=10)

    description = (
        ydb.TableDescription().with_primary_keys('key1', 'key2').with_columns(
            ydb.Column('key1', ydb.OptionalType(ydb.PrimitiveType.Uint64)),
            ydb.Column('key2', ydb.OptionalType(ydb.PrimitiveType.Uint64)),
            ydb.Column('value', ydb.OptionalType(ydb.PrimitiveType.Utf8))
        ).with_profile(

            ydb.TableProfile().with_partitioning_policy(

                ydb.PartitioningPolicy().with_explicit_partitions(

                    ydb.ExplicitPartitions(
                        (
                            ydb.KeyBound((100,)), ydb.KeyBound((300, 100)), ydb.KeyBound((400,)),
                        )
                    )
                )
            )
        )
    )

    session = await driver.table_client.session().create()
    await session.create_table(
        database + "/some_table",
        description
    )

    response = await session.describe_table(database + "/some_table")
    assert [c.name for c in response.columns] == ['key1', 'key2', 'value']


@pytest.mark.asyncio
async def test_raises_when_disconnect(endpoint, database, docker_project):

    driver_config = ydb.DriverConfig(
        endpoint, database, credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    driver = Driver(driver_config=driver_config)

    await driver.wait(timeout=10)

    async def restart_docker():
        docker_project.restart()

    coros = [
        driver.scheme_client.make_directory("/local/dir%i" % i)
        for i in range(100)
    ]
    coros.append(restart_docker())

    with pytest.raises(ydb.ConnectionLost):
        await asyncio.gather(*coros, return_exceptions=False)
