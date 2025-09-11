import ydb
import time
import logging
import threading
from random import choice
from typing import Union, Optional
from ratelimiter import RateLimiter

from metrics import Metrics, OP_TYPE_TOPIC_WRITE, OP_TYPE_TOPIC_READ

logger = logging.getLogger(__name__)


def run_topic_writes(driver, topic_path, metrics, limiter, runtime, timeout, message_size=100):
    """
    Запускает цикл записи сообщений в топик.

    :param driver: YDB driver
    :param topic_path: путь к топику
    :param metrics: объект для сбора метрик
    :param limiter: лимитер для RPS
    :param runtime: время работы в секундах
    :param timeout: таймаут операций в секундах
    :param message_size: размер сообщения в байтах
    """
    start_time = time.time()
    logger.info("Start topic write workload")

    with driver.topic_client.writer(topic_path) as writer:
        logger.info("Topic writer created")

        while time.time() - start_time < runtime:
            # Генерируем сообщение
            message_data = "x" * message_size

            with limiter:
                ts = metrics.start((OP_TYPE_TOPIC_WRITE,))
                error = None
                attempt = 1

                try:
                    # Записываем сообщение с подтверждением
                    writer.write(ydb.TopicWriterMessage(data=message_data), timeout=timeout)
                    logger.debug("Topic write message: %s", message_data)
                except ydb.Error as err:
                    error = err
                    logger.debug("Topic write error: %s", err)
                except BaseException as err:
                    error = err
                    logger.exception("Unexpected topic write error:")

                metrics.stop((OP_TYPE_TOPIC_WRITE,), ts, attempts=attempt, error=error)

    logger.info("Stop topic write workload")


def run_topic_reads(driver, topic_path, consumer_name, metrics, limiter, runtime, timeout):
    """
    Запускает цикл чтения сообщений из топика.

    :param driver: YDB driver
    :param topic_path: путь к топику
    :param consumer_name: имя консьюмера
    :param metrics: объект для сбора метрик
    :param limiter: лимитер для RPS
    :param runtime: время работы в секундах
    :param timeout: таймаут операций в секундах
    """
    start_time = time.time()
    logger.info("Start topic read workload")

    with driver.topic_client.reader(topic_path, consumer_name) as reader:
        logger.info("Topic reader created")

        while time.time() - start_time < runtime:
            with limiter:
                ts = metrics.start((OP_TYPE_TOPIC_READ,))
                error = None
                attempt = 1

                try:
                    # Читаем сообщение с таймаутом
                    message = reader.receive_message(timeout=timeout)
                    if message:
                        logger.debug("Topic read message: %s", message.data.decode())
                        # Коммитим сообщение
                        reader.commit(message)
                except ydb.Error as err:
                    error = err
                    logger.debug("Topic read error: %s", err)
                except TimeoutError:
                    # Таймаут - нормальная ситуация, не считаем ошибкой
                    error = None
                except BaseException as err:
                    error = err
                    logger.exception("Unexpected topic read error:")

                metrics.stop((OP_TYPE_TOPIC_READ,), ts, attempts=attempt, error=error)

    logger.info("Stop topic read workload")


def run_topic_write_jobs(args, driver, topic_path, metrics):
    """
    Запускает потоки для записи в топик.

    :param args: аргументы командной строки
    :param driver: YDB driver
    :param topic_path: путь к топику
    :param metrics: объект для сбора метрик
    :return: список Future объектов
    """
    logger.info("Start topic write jobs")

    write_limiter = RateLimiter(max_calls=args.topic_write_rps, period=1)

    futures = []
    for i in range(args.topic_write_threads):
        future = threading.Thread(
            name=f"slo_topic_write_{i}",
            target=run_topic_writes,
            args=(
                driver,
                topic_path,
                metrics,
                write_limiter,
                args.time,
                args.topic_write_timeout / 1000,
                args.topic_message_size
            ),
        )
        future.start()
        futures.append(future)

    return futures


def run_topic_read_jobs(args, driver, topic_path, consumer_name, metrics):
    """
    Запускает потоки для чтения из топика.

    :param args: аргументы командной строки
    :param driver: YDB driver
    :param topic_path: путь к топику
    :param consumer_name: имя консьюмера
    :param metrics: объект для сбора метрик
    :return: список Future объектов
    """
    logger.info("Start topic read jobs")

    read_limiter = RateLimiter(max_calls=args.topic_read_rps, period=1)

    futures = []
    for i in range(args.topic_read_threads):
        future = threading.Thread(
            name=f"slo_topic_read_{i}",
            target=run_topic_reads,
            args=(
                driver,
                topic_path,
                consumer_name,
                metrics,
                read_limiter,
                args.time,
                args.topic_read_timeout / 1000
            ),
        )
        future.start()
        futures.append(future)

    return futures


def create_topic(driver, topic_path, consumer_name, min_partitions=1, max_partitions=10, retention_hours=24):
    """
    Создает топик и консьюмера для SLO тестов.

    :param driver: YDB driver
    :param topic_path: путь к топику
    :param consumer_name: имя консьюмера
    :param min_partitions: минимальное количество активных партиций
    :param max_partitions: максимальное количество активных партиций
    :param retention_hours: время хранения данных в часах
    """
    logger.info("Creating topic: %s", topic_path)

    import datetime

    try:
        # Создаем топик
        driver.topic_client.create_topic(
            path=topic_path,
            min_active_partitions=min_partitions,
            max_active_partitions=max_partitions,
            retention_period=datetime.timedelta(hours=retention_hours),
            consumers=[consumer_name]
        )
        logger.info("Topic created successfully: %s", topic_path)
        logger.info("Consumer created: %s", consumer_name)

    except ydb.Error as e:
        error_msg = str(e).lower()
        if "already exists" in error_msg:
            logger.info("Topic already exists: %s", topic_path)

            # Проверяем, есть ли консьюмер
            try:
                description = driver.topic_client.describe_topic(topic_path)
                consumer_exists = any(c.name == consumer_name for c in description.consumers)

                if not consumer_exists:
                    logger.info("Adding consumer %s to existing topic", consumer_name)
                    driver.topic_client.alter_topic(
                        path=topic_path,
                        add_consumers=[consumer_name]
                    )
                    logger.info("Consumer added successfully: %s", consumer_name)
                else:
                    logger.info("Consumer already exists: %s", consumer_name)

            except Exception as alter_err:
                logger.warning("Failed to add consumer: %s", alter_err)
                raise
        elif "storage pool" in error_msg or "pq" in error_msg:
            logger.error("YDB instance does not support topics (PersistentQueues): %s", e)
            logger.error("Please use YDB instance with topic support")
            raise
        else:
            logger.error("Failed to create topic: %s", e)
            raise


def setup_topic(driver, topic_path, consumer_name):
    """
    Проверяет существование топика и консьюмера перед запуском SLO тестов.

    :param driver: YDB driver
    :param topic_path: путь к топику
    :param consumer_name: имя консьюмера
    """
    logger.info("Checking topic setup: %s", topic_path)

    try:
        description = driver.topic_client.describe_topic(topic_path)
        logger.info("Topic exists: %s", topic_path)

        # Проверяем, есть ли консьюмер
        consumer_exists = any(c.name == consumer_name for c in description.consumers)

        if consumer_exists:
            logger.info("Consumer exists: %s", consumer_name)
        else:
            logger.error("Consumer '%s' does not exist in topic '%s'", consumer_name, topic_path)
            logger.error("Please create the consumer first using topic-create command")
            raise RuntimeError(f"Consumer '{consumer_name}' not found")

    except ydb.Error as e:
        error_msg = str(e).lower()
        if "does not exist" in error_msg:
            logger.error("Topic does not exist: %s", topic_path)
            logger.error("Please create the topic first using topic-create command")
            raise RuntimeError(f"Topic '{topic_path}' not found")
        elif "storage pool" in error_msg or "pq" in error_msg:
            logger.error("YDB instance does not support topics (PersistentQueues): %s", e)
            logger.error("Please use YDB instance with topic support")
            raise
        else:
            logger.error("Failed to check topic: %s", e)
            raise


def cleanup_topic(driver, topic_path):
    """
    Удаляет топик.

    :param driver: YDB driver
    :param topic_path: путь к топику
    """
    logger.info("Cleaning up topic: %s", topic_path)

    try:
        driver.topic_client.drop_topic(topic_path)
        logger.info("Topic dropped: %s", topic_path)
    except ydb.Error as e:
        if "not found" in str(e).lower():
            logger.info("Topic does not exist: %s", topic_path)
        else:
            logger.error("Failed to drop topic: %s", e)
            raise
