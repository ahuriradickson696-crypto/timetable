import asyncio
from app.db.mongodb import init_mongodb, close_mongodb, users_col


async def main():
    await init_mongodb()

    # Promote admin@aviu.ac.ug to admin role
    result = await users_col().update_one(
        {"email": "admin@aviu.ac.ug"},
        {"$set": {"role": "admin", "is_active": True}},
    )
    print(f"Matched: {result.matched_count}, Modified: {result.modified_count}")

    # Show all users
    print()
    print("Current users:")
    async for u in users_col().find():
        print(f"  {u['email']:35} | role={u.get('role'):10} | _id={u['_id']}")

    await close_mongodb()


asyncio.run(main())