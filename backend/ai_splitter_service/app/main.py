import asyncio
import json
from bson import ObjectId
import aio_pika
from core.database import connect_to_mongo, close_mongo_connection, get_database
from core.rabbitmq import connect_to_rabbitmq, close_rabbitmq_connection, consume_messages
from core.gemini_ai import get_smart_split

async def process_expense_created(message: aio_pika.IncomingMessage):
    async with message.process():
        print(f"AI Splitter: Received message: {message.body.decode()}")
        try:
            expense_data = json.loads(message.body.decode())
            expense_id = expense_data.get("expense_id")
            group_id = expense_data.get("group_id")

            if not expense_id or not group_id:
                print("Invalid expense_created event: missing expense_id or group_id")
                return

            db = get_database()

            # Fetch group members to provide context for AI
            group_doc = await db["groups"].find_one({"_id": ObjectId(group_id)})
            if not group_doc:
                print(f"Group {group_id} not found for expense {expense_id}. Cannot smart split.")
                return
            
            group_members = group_doc.get("members", [])

            # Get smart split from AI
            smart_split = await get_smart_split(expense_data, group_members)
            
            # Update the expense in MongoDB
            update_result = await db["expenses"].update_one(
                {"_id": ObjectId(expense_id)},
                {"$set": {"split": smart_split}}
            )

            if update_result.modified_count > 0:
                print(f"Successfully updated expense {expense_id} with smart split: {smart_split}")
            else:
                print(f"Failed to update expense {expense_id} (expense not found or no change).")

        except json.JSONDecodeError:
            print("Error: Received malformed JSON message.")
        except Exception as e:
            print(f"Error processing expense_created event: {e}")

async def main():
    connect_to_mongo()
    await connect_to_rabbitmq()
    
    # Start consuming messages
    await consume_messages("ai_splitter_queue", process_expense_created)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("AI Splitter Service shutting down.")
        asyncio.run(close_rabbitmq_connection())
        close_mongo_connection()