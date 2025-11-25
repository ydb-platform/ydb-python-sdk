import ydb
import pyarrow as pa

def main():
    driver_config = ydb.DriverConfig(
        endpoint="grpc://localhost:2136",
        database="/local",
        # credentials=ydb.credentials_from_env_variables(),
        # root_certificates=ydb.load_ydb_root_certificate(),
    )

    try:
        driver = ydb.Driver(driver_config)
        driver.wait(timeout=5)
    except TimeoutError:
        raise RuntimeError("Connect failed to YDB")

    pool = ydb.QuerySessionPool(driver)

    query = """
        SELECT * FROM example ORDER BY key LIMIT 100;
    """

    format_settings = ydb.ArrowFormatSettings(
        compression_codec=ydb.ArrowCompressionCodec(ydb.ArrowCompressionCodecType.ZSTD, 10)
    )

    result = pool.execute_with_retries(
        query,
        result_set_format=ydb.QueryResultSetFormat.ARROW,
        arrow_format_settings=format_settings,
    )

    for result_set in result:
        schema: pa.Schema = pa.ipc.read_schema(pa.py_buffer(result_set.arrow_format_meta.schema))
        batch: pa.RecordBatch = pa.ipc.read_record_batch(pa.py_buffer(result_set.data), schema)
        print(f"Record batch with {batch.num_rows} rows and {batch.num_columns} columns")


if __name__ == "__main__":
    main()
