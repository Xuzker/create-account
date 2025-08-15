import asyncio
from fastapi import FastAPI
from app.api import endpoints
from app.kafka import kafka_consumer_task

app = FastAPI()

app.include_router(endpoints.router)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(kafka_consumer_task())