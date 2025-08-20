import asyncio
from fastapi import FastAPI
from app.api import endpoints
from app.kafka import kafka_consumer_task
from app.database import Base, engine

app = FastAPI()

app.include_router(endpoints.router)

@app.on_event("startup")
async def startup_event():
    # создаём таблицы при запуске
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # запускаем Kafka-консьюмера
    asyncio.create_task(kafka_consumer_task())
