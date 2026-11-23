import datetime
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated

import ydb


@dataclass
class OrderKey:
    order_id: Annotated[
        int,
        ydb.ModelField(
            ydb_type=ydb.PrimitiveType.Uint64,
            column_name="id",
        ),
    ]


@dataclass
class Order(OrderKey):
    customer: str
    amount: Annotated[
        Decimal,
        ydb.ModelField(ydb_type=ydb.DecimalType(22, 2)),
    ]
    created_at: datetime.datetime


def main() -> None:
    endpoint = os.getenv("YDB_ENDPOINT", "grpc://localhost:2136")
    database = os.getenv("YDB_DATABASE", "/local")
    table_path = f"{database}/typed_models_orders"

    config = ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
        credentials=ydb.credentials_from_env_variables(),
        type_mapping={
            datetime.datetime: ydb.PrimitiveType.Datetime64,
        },
    )

    with ydb.Driver(config) as driver:
        driver.wait(timeout=5, fail_fast=True)
        pool = ydb.QuerySessionPool(driver)

        pool.execute_with_retries(f"DROP TABLE IF EXISTS `{table_path}`")
        pool.execute_with_retries(f"""
            CREATE TABLE `{table_path}` (
                id Uint64 NOT NULL,
                customer Utf8 NOT NULL,
                amount Decimal(22, 2) NOT NULL,
                created_at Datetime64 NOT NULL,
                PRIMARY KEY (id)
            )
            """)

        orders = [
            Order(1, "alice", Decimal("10.50"), datetime.datetime(2025, 1, 1, 9, 15)),
            Order(2, "bob", Decimal("20.00"), datetime.datetime(2025, 1, 2, 10, 30)),
        ]

        driver.table_client.bulk_upsert(table_path, orders)

        result_sets = pool.execute_with_retries(
            """
            DECLARE $orders AS List<Struct<
                id: Uint64,
                customer: Utf8,
                amount: Decimal(22, 2),
                created_at: Datetime64
            >>;
            SELECT * FROM AS_TABLE($orders) ORDER BY id;
            """,
            parameters={"$orders": orders},
        )
        print("Query parameter round-trip:", result_sets[0].rows_as(Order))

        empty_result = pool.execute_with_retries(
            """
            DECLARE $orders AS List<Struct<
                id: Uint64,
                customer: Utf8,
                amount: Decimal(22, 2),
                created_at: Datetime64
            >>;
            SELECT COUNT(*) AS count FROM AS_TABLE($orders);
            """,
            parameters={"$orders": ydb.ModelValue([], list[Order])},
        )
        print("Empty typed parameter count:", empty_result[0].rows[0].count)

        selected = driver.table_client.read_rows(table_path, [OrderKey(2)])
        print("read_rows:", selected.rows_as(Order))

        session = driver.table_client.session().create()
        try:
            for result_set in session.read_table(table_path, ordered=True):
                print("read_table:", result_set.rows_as(Order))
        finally:
            session.delete()

        try:
            from pydantic import BaseModel
        except ImportError:
            return

        class PydanticOrder(BaseModel):
            order_id: Annotated[
                int,
                ydb.ModelField(
                    ydb_type=ydb.PrimitiveType.Uint64,
                    column_name="id",
                ),
            ]
            customer: str
            amount: Annotated[
                Decimal,
                ydb.ModelField(ydb_type=ydb.DecimalType(22, 2)),
            ]
            created_at: datetime.datetime

        print("Pydantic:", result_sets[0].rows_as(PydanticOrder))


if __name__ == "__main__":
    main()
