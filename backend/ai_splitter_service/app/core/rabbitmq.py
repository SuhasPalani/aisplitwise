import aio_pika
import asyncio
from core.config import settings

connection = None
channel = None

async def connect_to_rabbitmq():
    global connection, channel
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        print(f"AI Splitter Service: Connected to RabbitMQ at {settings.RABBITMQ_URL}")
        return channel
    except aio_pika.exceptions.AMQPConnectionError as e:
        print(f"AI Splitter Service: Could not connect to RabbitMQ: {e}")
        return None

async def close_rabbitmq_connection():
    global connection
    if connection:
        await connection.close()
        print("AI Splitter Service: RabbitMQ connection closed.")

async def consume_messages(queue_name: str, callback):
    global channel
    if not channel:
        print("RabbitMQ channel not available for consumption.")
        return

    # Ensure exchange and queue are declared (idempotent operations)
    exchange = await channel.declare_exchange("expense_events", aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.bind(exchange, "expense.created") # Bind to the specific routing key

    print(f"AI Splitter Service: Consuming from queue: {queue_name}")
    await queue.consume(callback)
    await asyncio.Future() # Run forever