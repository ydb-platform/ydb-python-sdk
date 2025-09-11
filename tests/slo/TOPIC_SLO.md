# YDB Python SDK Topic SLO Tests

Этот документ описывает как использовать SLO тесты для топиков YDB.

## Описание

Topic SLO тесты измеряют производительность операций с топиками YDB:
- **TopicWriter** - запись сообщений в топик
- **TopicReader** - чтение сообщений из топика с коммитом

Тесты собирают метрики:
- Latency (задержка операций)
- RPS (количество операций в секунду)
- Error rate (процент ошибок)
- Retry attempts (количество попыток повтора)

## Использование

### Запуск Topic SLO тестов

Topic SLO тесты автоматически создают топик перед началом тестирования и удаляют его после завершения:

```bash
cd tests/slo
python -m src topic-run grpc://localhost:2135 /local
```

### Параметры

#### Основные параметры:
- `endpoint` - YDB endpoint (например: `grpc://localhost:2135`)
- `db` - база данных (например: `/local`)

#### Параметры для топиков:
- `--topic-path` - путь к топику (по умолчанию: `/local/slo_topic`)
- `--topic-consumer` - имя консьюмера (по умолчанию: `slo_consumer`)
- `--topic-message-size` - размер сообщения в байтах (по умолчанию: 100)

#### Параметры производительности:
- `--topic-write-rps` - RPS для записи (по умолчанию: 20)
- `--topic-read-rps` - RPS для чтения (по умолчанию: 50)
- `--topic-write-threads` - количество потоков записи (по умолчанию: 2)
- `--topic-read-threads` - количество потоков чтения (по умолчанию: 4)

#### Таймауты:
- `--topic-write-timeout` - таймаут записи в мс (по умолчанию: 10000)
- `--topic-read-timeout` - таймаут чтения в мс (по умолчанию: 5000)

#### Временные параметры:
- `--time` - время работы теста в секундах (по умолчанию: 60)
- `--shutdown-time` - время на graceful shutdown в секундах (по умолчанию: 10)

#### Метрики:
- `--prom-pgw` - Prometheus push gateway (по умолчанию: `localhost:9091`)
- `--report-period` - период отправки метрик в мс (по умолчанию: 1000)

### Примеры использования

#### Базовый запуск с настройками по умолчанию:
```bash
python -m src topic-run grpc://localhost:2135 /local
```

#### Запуск с повышенной нагрузкой:
```bash
python -m src topic-run grpc://localhost:2135 /local \
  --topic-write-rps 100 \
  --topic-read-rps 200 \
  --topic-write-threads 4 \
  --topic-read-threads 8 \
  --time 300
```

#### Запуск с большими сообщениями:
```bash
python -m src topic-run grpc://localhost:2135 /local \
  --topic-message-size 1024 \
  --topic-write-rps 10 \
  --topic-read-rps 20
```

#### Запуск с кастомным топиком и консьюмером:
```bash
python -m src topic-run grpc://localhost:2135 /local \
  --topic-path /local/my_slo_topic \
  --topic-consumer my_consumer
```

## Архитектура

### Компоненты

1. **topic_jobs.py** - основная логика для работы с топиками:
   - `run_topic_writes()` - цикл записи сообщений
   - `run_topic_reads()` - цикл чтения сообщений
   - `setup_topic()` - создание топика и консьюмера
   - `cleanup_topic()` - очистка топика

2. **metrics.py** - расширен для поддержки топик метрик:
   - `OP_TYPE_TOPIC_WRITE` - метрики записи
   - `OP_TYPE_TOPIC_READ` - метрики чтения

3. **options.py** - добавлена команда `topic-run` с параметрами для топиков

4. **runner.py** - добавлена функция `run_topic_slo()` для запуска топик тестов

### Workflow

1. **Инициализация**: создание топика и консьюмера (если не существуют)
2. **Запуск воркеров**:
   - Потоки записи создают и отправляют сообщения
   - Потоки чтения получают и коммитят сообщения
3. **Сбор метрик**: все операции измеряются и отправляются в Prometheus
4. **Завершение**: graceful shutdown всех воркеров

## Метрики

Топик SLO тесты создают следующие метрики:

### Counters
- `sdk_operations_total{operation_type="topic_write"}` - общее количество операций записи
- `sdk_operations_total{operation_type="topic_read"}` - общее количество операций чтения
- `sdk_operations_success_total{operation_type="topic_write|topic_read"}` - успешные операции
- `sdk_operations_failure_total{operation_type="topic_write|topic_read"}` - неуспешные операции
- `sdk_errors_total{operation_type="topic_write|topic_read", error_type="ErrorType"}` - ошибки по типам

### Histograms
- `sdk_operation_latency_seconds{operation_type="topic_write|topic_read", operation_status="success|err"}` - латентность операций

### Gauges
- `sdk_pending_operations{operation_type="topic_write|topic_read"}` - количество операций в процессе
- `sdk_retry_attempts{operation_type="topic_write|topic_read"}` - количество попыток повтора

## Мониторинг

Для мониторинга рекомендуется использовать Grafana с Prometheus. Примеры запросов:

### RPS записи в топик:
```promql
rate(sdk_operations_total{operation_type="topic_write"}[1m])
```

### RPS чтения из топика:
```promql
rate(sdk_operations_total{operation_type="topic_read"}[1m])
```

### Процент ошибок записи:
```promql
rate(sdk_operations_failure_total{operation_type="topic_write"}[1m]) /
rate(sdk_operations_total{operation_type="topic_write"}[1m]) * 100
```

### 95-й перцентиль латентности чтения:
```promql
histogram_quantile(0.95, rate(sdk_operation_latency_seconds_bucket{operation_type="topic_read", operation_status="success"}[1m]))
```

## Troubleshooting

### Часто встречающиеся проблемы:

1. **Топик не создается**: проверьте права доступа и корректность пути к топику
2. **Таймауты чтения**: нормально, если нет новых сообщений; увеличьте `--topic-read-timeout` если нужно
3. **Высокий error rate**: проверьте подключение к YDB и лимиты топика
4. **Низкий RPS**: увеличьте количество потоков или RPS лимиты

### Логи:
Тесты логируют в уровне INFO основные события. Для подробной диагностики включите DEBUG:
```bash
export PYTHONPATH=src
python -c "import logging; logging.basicConfig(level=logging.DEBUG)" -m src topic-run ...
```
