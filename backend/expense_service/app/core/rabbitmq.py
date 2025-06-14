import aio_pika
import asyncio
from app.core.config import settings

connection = None
channel = None

async def connect_to_rabbitmq(retries: int = 10, delay: int = 5):
    global connection, channel

    for attempt in range(1, retries + 1):
        try:
            print(f"[RabbitMQ] Attempt {attempt} to connect to {settings.RABBITMQ_URL}")
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            channel = await connection.channel()
            print(f"[RabbitMQ] ✅ Connected to RabbitMQ at {settings.RABBITMQ_URL}")
            return
        except aio_pika.exceptions.AMQPConnectionError as e:
            print(f"[RabbitMQ] ❌ Connection failed: {e}")
            if attempt == retries:
                print("[RabbitMQ] ❌ Max retries reached. Exiting.")
                exit(1)
            await asyncio.sleep(delay)

async def close_rabbitmq_connection():
    global connection
    if connection:
        await connection.close()
        print("[RabbitMQ] 🔒 Connection closed.")

async def publish_message(exchange_name: str, routing_key: str, message: str):
    if not channel:
        print("[RabbitMQ] ⚠️ Channel not available. Message not published.")
        return

    exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
    await exchange.publish(
        aio_pika.Message(body=message.encode()),
        routing_key=routing_key
    )
    print(f"[RabbitMQ] 📤 Published to {exchange_name} [{routing_key}]: {message}")
