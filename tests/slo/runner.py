import ydb

from os import path
from generator import PackGenerator

from prometheus_client import Summary, Counter


def run_create(args, driver):
    session = ydb.retry_operation_sync(lambda: driver.table_client.session().create())
    tb_name = path.join(args.db, args.table_name)
    session.create_table(
        tb_name,
        ydb.TableDescription()
        .with_column(ydb.Column("object_id_key", ydb.OptionalType(ydb.PrimitiveType.Uint32)))
        .with_column(ydb.Column("object_id", ydb.OptionalType(ydb.PrimitiveType.Uint32)))
        .with_column(ydb.Column("payload_str", ydb.OptionalType(ydb.PrimitiveType.Utf8)))
        .with_column(ydb.Column("payload_double", ydb.OptionalType(ydb.PrimitiveType.Double)))
        .with_column(ydb.Column("payload_timestamp", ydb.OptionalType(ydb.PrimitiveType.Timestamp)))
        .with_primary_keys("object_id_key", "object_id")
        .with_profile(
            ydb.TableProfile().with_partitioning_policy(
                ydb.PartitioningPolicy().with_uniform_partitions(args.partitions_count)
            )
        ),
    )

    prepare_q = """
    DECLARE $items AS List<Struct<
        object_id_key: Uint32,
        object_id: Uint32,
        payload_str: Utf8,
        payload_double: Double,
        payload_timestamp: Timestamp>>;
    UPSERT INTO `{}` SELECT * FROM AS_TABLE($items);
    """
    prepared = session.prepare(prepare_q.format(tb_name))

    generator = PackGenerator(args)
    while data := generator.get_next_pack():
        tx = session.transaction()
        tx.execute(prepared, {"$items": data})
        tx.commit()


def run_cleanup(args, driver):
    session = driver.table_client.session().create()
    session.drop_table(path.join(args.db, args.table_name))


def run_from_args(args):
    driver_config = ydb.DriverConfig(
        args.endpoint,
        database=args.db,
        credentials=ydb.credentials_from_env_variables(),
        grpc_keep_alive_timeout=5000,
    )

    with ydb.Driver(driver_config) as driver:
        driver.wait(timeout=5)

        try:
            if args.subcommand == "create":
                run_create(args, driver)
            elif args.subcommand == "run":
                pass
            elif args.subcommand == "cleanup":
                run_cleanup(args, driver)
            else:
                raise RuntimeError(f"Unknown command {args.subcommand}")
        finally:
            driver.stop()
