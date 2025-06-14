import aio_pika
import asyncio
from app.core.config import settings

connection = None
channel = None

async def connect_to_rabbitmq():
    global connection, channel
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        print(f"Reporting Service: Connected to RabbitMQ at {settings.RABBITMQ_URL}")
        return channel
    except aio_pika.exceptions.AMQPConnectionError as e:
        print(f"Reporting Service: Could not connect to RabbitMQ: {e}")
        return None

async def close_rabbitmq_connection():
    global connection
    if connection:
        await connection.close()
        print("Reporting Service: RabbitMQ connection closed.")

async def consume_messages(queue_name: str, routing_key: str, callback):
    global channel
    if not channel:
        print("RabbitMQ channel not available for consumption.")
        return

    # Declare the exchange and bind the queue
    exchange = await channel.declare_exchange("expense_events", aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.bind(exchange, routing_key)

    print(f"Reporting Service: Consuming from queue: {queue_name} with routing key {routing_key}")
    await queue.consume(callback)
    await asyncio.Future() # Keep the consumer running indefinitely