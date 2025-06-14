import asyncio
import json
import aio_pika
from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.core.rabbitmq import connect_to_rabbitmq, close_rabbitmq_connection, consume_messages

async def process_expense_event(message: aio_pika.IncomingMessage):
    async with message.process():
        event_data = json.loads(message.body.decode())
        routing_key = message.routing_key
        print(f"Reporting Service: Received {routing_key} event: {event_data}")
        
        # Here you would typically process the event, e.g.:
        # - Aggregate data for monthly reports
        # - Update statistics in a reporting collection
        # - Trigger other analytics tasks
        # For this example, we just log it.
        
        # Example: Store raw events for later analysis
        # db = get_database()
        # await db["raw_events"].insert_one({"event_type": routing_key, "data": event_data, "timestamp": datetime.utcnow()})
        # print(f"Event stored for reporting: {routing_key}")

async def main():
    connect_to_mongo()
    await connect_to_rabbitmq()
    
    # Listen to all expense events (or specific ones like 'expense.created', 'expense.split_updated')
    # Use '#' wildcard for all topic messages under 'expense_events'
    await consume_messages("reporting_queue", "expense.#", process_expense_event)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Reporting Service shutting down.")
        asyncio.run(close_rabbitmq_connection())
        close_mongo_connection()