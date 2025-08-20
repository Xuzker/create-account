import asyncio
from confluent_kafka import Producer, Consumer, KafkaError

KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
KAFKA_TOPIC = 'test-topic'
KAFKA_GROUP_ID = 'fastapi-group'

producer_conf = {'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS}
producer = Producer(producer_conf)

def delivery_report(err, msg):
    if err:
        print(f"Ошибка доставки: {err}")
    else:
        print(f"Доставлено в {msg.topic()} [{msg.partition()}]")

consumer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': KAFKA_GROUP_ID,
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}

consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])

consumed_messages = []

async def kafka_consumer_task():
    loop = asyncio.get_event_loop()
    while True:
        msg = await loop.run_in_executor(None, consumer.poll, 1.0)
        if msg is None:
            await asyncio.sleep(0.1)
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(f"Ошибка консьюмера: {msg.error()}")
                continue
        value = msg.value().decode('utf-8')
        print(f"Получено сообщение: {value}")
        consumed_messages.append(value)
        if len(consumed_messages) > 100:
            consumed_messages.pop(0)

def produce_message(content: str):
    producer.produce(KAFKA_TOPIC, content.encode('utf-8'), callback=delivery_report)
    producer.poll(0)