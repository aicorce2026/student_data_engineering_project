from pathlib import Path
from pymongo import MongoClient
import json


# ==========================================================
# إعداد المسارات والاتصال
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "mongodb"
    / "students_mongodb_raw.json"
)

MONGO_URI = "mongodb://127.0.0.1:27017/"

DATABASE_NAME = "student_data_engineering"

COLLECTION_NAME = "students_raw"


# ==========================================================
# قراءة ملف JSON الخام
# ==========================================================

def load_raw_json():

    # قراءة البيانات كما هي بدون تنظيف أو تعديل
    with RAW_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    # التأكد أن الملف يحتوي قائمة سجلات
    if not isinstance(data, list):

        raise ValueError(
            "يجب أن يحتوي ملف JSON على قائمة من السجلات"
        )

    print(
        "تم قراءة",
        len(data),
        "سجلات من ملف JSON"
    )

    return data


# ==========================================================
# الاتصال بـ MongoDB
# ==========================================================

def connect_mongodb():

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    # اختبار الاتصال
    client.admin.command("ping")

    print("تم الاتصال بـ MongoDB بنجاح")

    return client


# ==========================================================
# إدخال البيانات الخام
# ==========================================================

def seed_raw_data(
    client,
    data
):

    database = client[
        DATABASE_NAME
    ]

    collection = database[
        COLLECTION_NAME
    ]

    # التحقق هل تم إدخال البيانات من قبل
    existing_count = (
        collection.count_documents({})
    )

    if existing_count > 0:

        print(
            "Collection students_raw تحتوي بالفعل على",
            existing_count,
            "سجلات"
        )

        print(
            "لن نقوم بالحذف أو الإدخال مرة أخرى حفاظاً على البيانات الخام"
        )

        return

    # إدخال البيانات كما هي
    result = collection.insert_many(
        data
    )

    print(
        "تم إدخال",
        len(result.inserted_ids),
        "سجلات إلى MongoDB"
    )


# ==========================================================
# التشغيل
# ==========================================================

def main():

    print(
        "\n========== MONGODB RAW DATA SEED =========="
    )

    data = load_raw_json()

    client = connect_mongodb()

    try:

        seed_raw_data(
            client,
            data
        )

    finally:

        client.close()

        print(
            "تم إغلاق الاتصال بـ MongoDB"
        )

    print(
        "========== SEED COMPLETED =========="
    )


if __name__ == "__main__":
    main()