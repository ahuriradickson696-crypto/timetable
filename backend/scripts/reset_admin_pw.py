import asyncio
from app.db.mongodb import init_mongodb, close_mongodb, users_col
from app.core.security import hash_password, verify_password


async def main():
    await init_mongodb()

    new_pw = "admin123"
    hashed = hash_password(new_pw)

    r = await users_col().update_one(
        {"email": "admin@aviu.ac.ug"},
        {"$set": {"hashed_password": hashed, "role": "admin", "is_active": True}},
    )
    print("Matched:", r.matched_count, "| Modified:", r.modified_count)

    doc = await users_col().find_one({"email": "admin@aviu.ac.ug"})
    if not doc:
        print("User not found!")
        await close_mongodb()
        return

    ok = verify_password(new_pw, doc["hashed_password"])
    print("Password check:", "OK" if ok else "FAIL")
    print()
    print("User record:")
    print("  email:  " + doc["email"])
    print("  role:   " + doc["role"])
    print("  active: " + str(doc["is_active"]))
    print("  hash:   " + doc["hashed_password"][:25] + "...")

    await close_mongodb()


asyncio.run(main())