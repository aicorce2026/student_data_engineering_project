from pathlib import Path

import pandas as pd
from pymongo import MongoClient


# ==========================================================
# الإعدادات
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MONGO_URI = "mongodb://localhost:27017/"

DATABASE_NAME = "student_data_engineering"

RAW_COLLECTION = "students_raw"

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mongodb"
    / "students_clean.csv"
)

REPORT_FILE = (
    BASE_DIR
    / "reports"
    / "mongodb_quality_report.txt"
)


# ==========================================================
# الاتصال بـ MongoDB
# ==========================================================

def get_collection():

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command(
        "ping"
    )

    database = client[
        DATABASE_NAME
    ]

    collection = database[
        RAW_COLLECTION
    ]

    return client, collection


# ==========================================================
# قراءة البيانات
# ==========================================================

def read_students(
    collection
) -> list[dict]:

    return list(
        collection.find(
            {},
            {
                "_id": 0
            }
        )
    )


# ==========================================================
# استعلامات MongoDB
# ==========================================================

def show_queries(
    collection
) -> None:

    print(
        "\nStudents with GPA >= 3.5:"
    )

    students = collection.find(
        {
            "academic.gpa": {
                "$gte": 3.5
            }
        },
        {
            "_id": 0,
            "student_id": 1,
            "personal.name": 1,
            "academic.gpa": 1
        }
    )

    for student in students:
        print(
            student
        )

    print(
        "\nStudents with Python skill:"
    )

    students = collection.find(
        {
            "skills": "Python"
        },
        {
            "_id": 0,
            "student_id": 1,
            "personal.name": 1,
            "skills": 1
        }
    )

    for student in students:
        print(
            student
        )


# ==========================================================
# Aggregation
# ==========================================================

def show_aggregation(
    collection
) -> None:

    pipeline = [
        {
            "$group": {
                "_id": "$personal.city",
                "students_count": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "students_count": -1
            }
        }
    ]

    print(
        "\nStudents by city:"
    )

    for item in collection.aggregate(
        pipeline
    ):
        print(
            item
        )


# ==========================================================
# تحويل MongoDB إلى DataFrame
# ==========================================================

def transform_to_dataframe(
    records: list[dict]
) -> pd.DataFrame:

    return pd.json_normalize(
        records
    )


# ==========================================================
# تنظيف البيانات
# ==========================================================

def clean_data(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    # حذف Student ID المكرر
    df = df.drop_duplicates(
        subset=["student_id"],
        keep="first"
    )

    # تنظيف النصوص
    df["personal.name"] = (
        df["personal.name"]
        .astype("string")
        .str.strip()
    )

    df["personal.city"] = (
        df["personal.city"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    # تحويل البيانات الرقمية
    numeric_columns = [
        "personal.age",
        "academic.gpa",
        "academic.attendance"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # تحديد القيم غير الصحيحة
    df["personal.age"] = (
        df["personal.age"].where(
            df["personal.age"].between(
                16,
                80
            )
        )
    )

    df["academic.gpa"] = (
        df["academic.gpa"].where(
            df["academic.gpa"].between(
                0,
                4
            )
        )
    )

    df["academic.attendance"] = (
        df["academic.attendance"].where(
            df["academic.attendance"].between(
                0,
                100
            )
        )
    )

    # معالجة القيم المفقودة
    for column in numeric_columns:

        df[column] = (
            df[column]
            .fillna(
                df[column].median()
            )
        )

    # Feature بسيطة من Unit 8
    df["python_skill"] = (
        df["skills"]
        .apply(
            lambda skills:
            "Python" in skills
            if isinstance(
                skills,
                list
            )
            else False
        )
    )

    return df


# ==========================================================
# التحقق من البيانات
# ==========================================================

def validate_dataframe(
    df: pd.DataFrame
) -> None:

    required_columns = {
        "student_id",
        "personal.name",
        "academic.gpa"
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:

        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    if df.empty:

        raise ValueError(
            "DataFrame is empty."
        )

    if not df[
        "student_id"
    ].is_unique:

        raise ValueError(
            "student_id must be unique."
        )

    if not df[
        "academic.gpa"
    ].between(
        0,
        4
    ).all():

        raise ValueError(
            "Invalid GPA values."
        )

    if not df[
        "academic.attendance"
    ].between(
        0,
        100
    ).all():

        raise ValueError(
            "Invalid attendance values."
        )


# ==========================================================
# حفظ البيانات
# ==========================================================

def save_data(
    df: pd.DataFrame
) -> None:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )


# ==========================================================
# تقرير بسيط
# ==========================================================

def save_report(
    raw_count: int,
    df: pd.DataFrame
) -> None:

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report = (
        "MONGODB DATA REPORT\n"
        "===================\n"
        f"Raw documents: {raw_count}\n"
        f"Final students: {len(df)}\n"
        f"Columns: {len(df.columns)}\n"
        "Validation: PASSED\n"
    )

    REPORT_FILE.write_text(
        report,
        encoding="utf-8"
    )


# ==========================================================
# تشغيل الـ Pipeline
# ==========================================================

def main():

    client = None

    try:

        client, collection = (
            get_collection()
        )

        print(
            "Connected to MongoDB."
        )

        raw_count = (
            collection.count_documents({})
        )

        print(
            f"Raw documents: {raw_count}"
        )

        # MongoDB Queries
        show_queries(
            collection
        )

        # MongoDB Aggregation
        show_aggregation(
            collection
        )

        # Extract
        records = read_students(
            collection
        )

        # MongoDB -> Pandas
        df = transform_to_dataframe(
            records
        )

        # Cleaning
        df = clean_data(
            df
        )

        # Validation
        validate_dataframe(
            df
        )

        # Save
        save_data(
            df
        )

        save_report(
            raw_count,
            df
        )

        print(
            "\nFinal MongoDB Data:"
        )

        print(
            df[
                [
                    "student_id",
                    "personal.name",
                    "personal.city",
                    "academic.gpa",
                    "python_skill"
                ]
            ]
        )

        print(
            "\nMongoDB Pipeline completed successfully."
        )

        print(
            f"Rows: {len(df)}"
        )

        print(
            f"Output: {OUTPUT_FILE}"
        )

    finally:

        if client is not None:

            client.close()


if __name__ == "__main__":
    main()