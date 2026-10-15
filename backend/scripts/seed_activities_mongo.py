import asyncio
from app.db.mongodb import init_mongodb, close_mongodb, cohorts_col, course_units_col, activities_col


def lecturer_for(code):
    c = code.upper()
    if " CS " in c or " IT " in c: return "LECT-004"
    if " BI " in c: return "LECT-005"
    if " CH " in c: return "LECT-006"
    if " MT " in c: return "LECT-007"
    if " PY " in c: return "LECT-008"
    if " AP " in c: return "LECT-010"
    if " BC " in c: return "LECT-011"
    if " MB " in c: return "LECT-012"
    if " CM " in c: return "LECT-016"
    if " CP " in c: return "LECT-017"
    if " LB " in c: return "LECT-018"
    if " HE " in c: return "LECT-020"
    if " ED " in c: return "LECT-002"
    return "LECT-001"


async def main():
    await init_mongodb()
    await activities_col().delete_many({})
    cohorts = await cohorts_col().find().to_list(50)
    created = 0
    for cohort in cohorts:
        prefix = cohort["programme_code"] + " "
        units = await course_units_col().find({
            "code": {"$regex": "^" + prefix},
            "normal_year": cohort["year_level"],
            "active": True,
        }).to_list(200)
        for u in units:
            act_id = cohort["id"] + "--" + u["code"].replace(" ", "_")
            await activities_col().insert_one({
                "id": act_id,
                "cohort_id": cohort["id"],
                "module_code": u["code"],
                "lecturer_id": lecturer_for(u["code"]),
                "duration_periods": max(1, (u.get("contact_hours_per_week") or 2) // 2),
                "preferred_room_type": u.get("preferred_room_type") or "Lecture",
                "students": cohort.get("estimated_students") or 30,
                "semester": cohort["semester"],
                "intake": cohort["intake"],
                "academic_year": cohort["academic_year"],
                "activity_type": "teaching",
            })
            created += 1
    print("Created " + str(created) + " activities")
    await close_mongodb()


asyncio.run(main())