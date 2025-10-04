import time
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import (
    Counter, Histogram, generate_latest,
    Gauge, PROCESS_COLLECTOR, PLATFORM_COLLECTOR, GC_COLLECTOR
)
from app.api import endpoints
from app.kafka import kafka_consumer_task
from app.database import Base, engine

app = FastAPI()
app.include_router(endpoints.router)

APP_NAME = "create-account"

# -------------------------------
# Метрики HTTP
# -------------------------------
FASTAPI_RESPONSES_TOTAL = Counter(
    "fastapi_responses_total",
    "Total number of HTTP responses",
    ["app_name", "method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency",
    ["app_name", "method", "endpoint"]
)

FASTAPI_EXCEPTIONS_TOTAL = Counter(
    "fastapi_exceptions_total",
    "Total number of exceptions",
    ["app_name", "exception_type"]
)

# -------------------------------
# Middleware для сбора HTTP метрик
# -------------------------------
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = str(response.status_code)
    except Exception as e:
        # считаем исключение
        FASTAPI_EXCEPTIONS_TOTAL.labels(
            app_name=APP_NAME,
            exception_type=type(e).__name__
        ).inc()
        raise
    finally:
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(
            app_name=APP_NAME,
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

    FASTAPI_RESPONSES_TOTAL.labels(
        app_name=APP_NAME,
        method=request.method,
        endpoint=request.url.path,
        status_code=status_code
    ).inc()

    return response

# -------------------------------
# Эндпоинт для Prometheus
# -------------------------------
@app.get("/metrics")
async def metrics():
    content = generate_latest()  # включает все метрики: пользовательские + стандартные
    return Response(content=content, media_type="text/plain")

# -------------------------------
# Событие startup
# -------------------------------
@app.on_event("startup")
async def startup_event():
    # создаём таблицы при запуске
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # запускаем Kafka-консьюмера
    asyncio.create_task(kafka_consumer_task())

# -------------------------------
# Регистрация стандартных метрик Python и процесса
# -------------------------------
# GC, платформа, процесс (CPU, память, FDs)
