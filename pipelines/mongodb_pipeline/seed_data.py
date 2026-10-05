from pathlib import Path
import json

from pymongo import MongoClient


# ==========================================================
# الإعدادات
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "mongodb"
    / "students_mongodb_raw.json"
)

MONGO_URI = "mongodb://localhost:27017/"

DATABASE_NAME = "student_data_engineering"

RAW_COLLECTION = "students_raw"

DEMO_COLLECTION = "students_crud_demo"


# ==========================================================
# قراءة JSON
# ==========================================================

def load_data() -> list[dict]:

    with RAW_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


# ==========================================================
# حفظ Raw Data في MongoDB
# ==========================================================

def seed_raw_data(
    database,
    data: list[dict]
) -> None:

    collection = database[
        RAW_COLLECTION
    ]

    count = collection.count_documents(
        {}
    )

    if count == 0:

        collection.insert_many(
            data
        )

        print(
            f"Inserted raw documents: {len(data)}"
        )

    else:

        print(
            f"Raw collection already has {count} documents."
        )


# ==========================================================
# CRUD Demo
# ==========================================================

def crud_demo(
    database
) -> None:

    collection = database[
        DEMO_COLLECTION
    ]

    # حذف نسخة Demo قديمة إن وجدت
    collection.delete_one(
        {
            "student_id": "DEMO001"
        }
    )

    # CREATE
    student = {
        "student_id": "DEMO001",
        "name": "Demo Student",
        "skills": [
            "Python",
            "MongoDB"
        ],
        "academic": {
            "gpa": 3.5,
            "attendance": 90
        }
    }

    collection.insert_one(
        student
    )

    print(
        "\nCREATE: Student inserted."
    )

    # READ
    result = collection.find_one(
        {
            "student_id": "DEMO001"
        },
        {
            "_id": 0
        }
    )

    print(
        "READ:",
        result
    )

    # UPDATE
    collection.update_one(
        {
            "student_id": "DEMO001"
        },
        {
            "$set": {
                "academic.gpa": 3.7
            }
        }
    )

    result = collection.find_one(
        {
            "student_id": "DEMO001"
        },
        {
            "_id": 0
        }
    )

    print(
        "UPDATE:",
        result
    )

    # DELETE
    collection.delete_one(
        {
            "student_id": "DEMO001"
        }
    )

    print(
        "DELETE: Demo student removed."
    )


# ==========================================================
# التشغيل
# ==========================================================

def main():

    client = None

    try:

        data = load_data()

        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        client.admin.command(
            "ping"
        )

        print(
            "Connected to MongoDB."
        )

        database = client[
            DATABASE_NAME
        ]

        seed_raw_data(
            database,
            data
        )

        crud_demo(
            database
        )

        print(
            "\nMongoDB seed and CRUD demo completed."
        )

    finally:

        if client is not None:

            client.close()


if __name__ == "__main__":
    main()