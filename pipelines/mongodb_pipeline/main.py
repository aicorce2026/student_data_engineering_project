from pathlib import Path
import json

import pandas as pd
from pymongo import MongoClient


# ==========================================================
# إعداد المشروع والاتصال
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MONGO_URI = "mongodb://127.0.0.1:27017/"

DATABASE_NAME = "student_data_engineering"

RAW_COLLECTION = "students_raw"
CLEAN_COLLECTION = "students_clean"

PROCESSED_FILE = (
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
# 1. الاتصال بـ MongoDB
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
# 2. فحص البيانات الخام
# ==========================================================

def inspect_raw_data(collection):

    print(
        "\n========== RAW MONGODB INSPECTION =========="
    )

    count = collection.count_documents({})

    print(
        "عدد السجلات الخام:",
        count
    )

    print(
        "\n========== أول سجلين =========="
    )

    records = list(
        collection.find(
            {},
            {"_id": 0}
        ).limit(2)
    )

    for record in records:
        print(record)


# ==========================================================
# 3. Nested Query
# البحث داخل الحقول المتداخلة
# ==========================================================

def run_nested_query(collection):

    print(
        "\n========== NESTED QUERY =========="
    )

    # البحث عن الطلاب الذين GPA لديهم أكبر من 3.5
    results = list(
        collection.find(
            {
                "academic.gpa": {
                    "$gt": 3.5
                }
            },
            {
                "_id": 0,
                "student_id": 1,
                "personal.name": 1,
                "academic.gpa": 1
            }
        )
    )

    print(
        "طلاب GPA أكبر من 3.5:"
    )

    for result in results:
        print(result)


# ==========================================================
# 4. Array Query
# البحث داخل Array
# ==========================================================

def run_array_query(collection):

    print(
        "\n========== ARRAY QUERY =========="
    )

    # البحث عن الطلاب الذين لديهم مهارة Python
    results = list(
        collection.find(
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
    )

    print(
        "الطلاب الذين لديهم مهارة Python:"
    )

    for result in results:
        print(result)


# ==========================================================
# 5. Aggregation
# تجميع البيانات حسب المدينة
# ==========================================================

def run_aggregation(collection):

    print(
        "\n========== AGGREGATION =========="
    )

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

    results = list(
        collection.aggregate(
            pipeline
        )
    )

    print(
        "عدد الطلاب حسب المدينة قبل التنظيف:"
    )

    for result in results:
        print(result)


# ==========================================================
# 6. Extract
# استخراج MongoDB إلى Pandas
# ==========================================================

def extract_to_dataframe(collection):

    documents = list(
        collection.find(
            {},
            {"_id": 0}
        )
    )

    if not documents:

        raise ValueError(
            "MongoDB لا تحتوي بيانات"
        )

    # تحويل Nested JSON إلى DataFrame
    df = pd.json_normalize(
        documents
    )

    print(
        "\nتم استخراج البيانات إلى DataFrame"
    )

    print(
        "الحجم:",
        df.shape
    )

    return df


# ==========================================================
# 7. اكتشاف مشاكل البيانات
# ==========================================================

def inspect_quality(df):

    print(
        "\n========== DATA QUALITY BEFORE CLEANING =========="
    )

    print(
        "\nالقيم المفقودة:"
    )

    print(
        df.isnull().sum()
    )

    print(
        "\nStudent IDs المكررة:"
    )

    print(
        df["student_id"]
        .duplicated()
        .sum()
    )

    print(
        "\nأنواع البيانات:"
    )

    print(
        df.dtypes
    )


# ==========================================================
# 8. Cleaning + Transformation
# ==========================================================

def clean_data(df):

    # العمل على نسخة حتى نحافظ على البيانات المستخرجة
    df = df.copy()

    # ------------------------------------------------------
    # تنظيف النصوص
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # تحويل أنواع البيانات الرقمية
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # معالجة العمر غير الصحيح
    # ------------------------------------------------------

    df.loc[
        ~df["personal.age"].between(
            16,
            80
        ),
        "personal.age"
    ] = pd.NA

    df["personal.age"] = (
        df["personal.age"]
        .fillna(
            df["personal.age"].median()
        )
    )

    # ------------------------------------------------------
    # معالجة GPA
    # ------------------------------------------------------

    df.loc[
        ~df["academic.gpa"].between(
            0,
            4
        ),
        "academic.gpa"
    ] = pd.NA

    df["academic.gpa"] = (
        df["academic.gpa"]
        .fillna(
            df["academic.gpa"].median()
        )
    )

    # ------------------------------------------------------
    # معالجة Attendance
    # ------------------------------------------------------

    df.loc[
        ~df["academic.attendance"].between(
            0,
            100
        ),
        "academic.attendance"
    ] = pd.NA

    df["academic.attendance"] = (
        df["academic.attendance"]
        .fillna(
            df["academic.attendance"].median()
        )
    )

    # ------------------------------------------------------
    # إزالة student_id المكرر
    # ------------------------------------------------------

    df = df.drop_duplicates(
        subset=["student_id"],
        keep="first"
    )

    # ------------------------------------------------------
    # Feature Engineering من Arrays
    # ------------------------------------------------------

    df["skills_count"] = (
        df["skills"]
        .apply(
            lambda value:
            len(value)
            if isinstance(value, list)
            else 0
        )
    )

    df["projects_count"] = (
        df["projects"]
        .apply(
            lambda value:
            len(value)
            if isinstance(value, list)
            else 0
        )
    )

    df["has_python"] = (
        df["skills"]
        .apply(
            lambda value:
            "Python" in value
            if isinstance(value, list)
            else False
        )
    )

    # ------------------------------------------------------
    # Feature إضافية
    # ------------------------------------------------------

    df["performance_score"] = (
        df["academic.gpa"]
        / 4
        * 100
    )

    return df


# ==========================================================
# 9. Validation
# ==========================================================

def validate_data(df):

    errors = []

    # student_id يجب أن يكون فريداً
    if df["student_id"].duplicated().any():

        errors.append(
            "يوجد student_id مكرر"
        )

    # student_id مطلوب
    if df["student_id"].isnull().any():

        errors.append(
            "يوجد student_id مفقود"
        )

    # الاسم مطلوب
    if df["personal.name"].isnull().any():

        errors.append(
            "يوجد اسم مفقود"
        )

    # العمر
    if not df["personal.age"].between(
        16,
        80
    ).all():

        errors.append(
            "يوجد عمر غير صالح"
        )

    # GPA
    if not df["academic.gpa"].between(
        0,
        4
    ).all():

        errors.append(
            "يوجد GPA غير صالح"
        )

    # Attendance
    if not df["academic.attendance"].between(
        0,
        100
    ).all():

        errors.append(
            "يوجد Attendance غير صالح"
        )

    if errors:

        print(
            "\nفشل التحقق من البيانات"
        )

        for error in errors:
            print("-", error)

        raise ValueError(
            "MongoDB validation failed"
        )

    print(
        "\nتم التحقق من بيانات MongoDB بنجاح"
    )


# ==========================================================
# 10. تحويل البيانات النظيفة مرة أخرى إلى Documents
# ==========================================================

def dataframe_to_documents(df):

    documents = []

    for _, row in df.iterrows():

        document = {

            "student_id":
                row["student_id"],

            "personal": {
                "name":
                    row["personal.name"],

                "age":
                    int(
                        row["personal.age"]
                    ),

                "city":
                    row["personal.city"]
            },

            "academic": {
                "gpa":
                    float(
                        row["academic.gpa"]
                    ),

                "attendance":
                    float(
                        row[
                            "academic.attendance"
                        ]
                    )
            },

            "skills":
                row["skills"],

            "projects":
                row["projects"],

            "features": {
                "skills_count":
                    int(
                        row["skills_count"]
                    ),

                "projects_count":
                    int(
                        row["projects_count"]
                    ),

                "has_python":
                    bool(
                        row["has_python"]
                    ),

                "performance_score":
                    float(
                        row[
                            "performance_score"
                        ]
                    )
            }
        }

        documents.append(
            document
        )

    return documents


# ==========================================================
# 11. حفظ Collection نظيفة
# ==========================================================

def save_clean_collection(
    database,
    documents
):

    clean_collection = database[
        CLEAN_COLLECTION
    ]

    # هذه Collection معالجة وليست البيانات الأصلية
    # لذلك يمكن إعادة بنائها عند تشغيل Pipeline
    clean_collection.delete_many({})

    if documents:

        clean_collection.insert_many(
            documents
        )

    print(
        "\nتم إنشاء Collection نظيفة:"
    )

    print(
        CLEAN_COLLECTION
    )

    print(
        "عدد السجلات:",
        clean_collection.count_documents({})
    )


# ==========================================================
# 12. حفظ CSV
# ==========================================================

def save_processed_csv(df):

    PROCESSED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # تحويل Arrays إلى JSON نصي حتى تحفظ بشكل واضح في CSV
    csv_df = df.copy()

    for column in [
        "skills",
        "projects"
    ]:

        csv_df[column] = (
            csv_df[column]
            .apply(
                lambda value:
                json.dumps(
                    value,
                    ensure_ascii=False
                )
            )
        )

    csv_df.to_csv(
        PROCESSED_FILE,
        index=False
    )

    print(
        "\nتم حفظ MongoDB Processed CSV:"
    )

    print(
        PROCESSED_FILE
    )


# ==========================================================
# 13. Quality Report
# ==========================================================

def create_quality_report(
    raw_df,
    clean_df
):

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    duplicate_ids = (
        raw_df["student_id"]
        .duplicated()
        .sum()
    )

    missing_gpa = (
        raw_df["academic.gpa"]
        .isnull()
        .sum()
    )

    missing_attendance = (
        raw_df[
            "academic.attendance"
        ]
        .isnull()
        .sum()
    )

    # تحويل مؤقت لغرض قياس الأخطاء الأصلية
    age_numeric = pd.to_numeric(
        raw_df["personal.age"],
        errors="coerce"
    )

    gpa_numeric = pd.to_numeric(
        raw_df["academic.gpa"],
        errors="coerce"
    )

    attendance_numeric = pd.to_numeric(
        raw_df[
            "academic.attendance"
        ],
        errors="coerce"
    )

    invalid_age = (
        age_numeric.notna()
        &
        ~age_numeric.between(
            16,
            80
        )
    ).sum()

    invalid_gpa = (
        gpa_numeric.notna()
        &
        ~gpa_numeric.between(
            0,
            4
        )
    ).sum()

    invalid_attendance = (
        attendance_numeric.notna()
        &
        ~attendance_numeric.between(
            0,
            100
        )
    ).sum()

    report = f"""
MONGODB DATA QUALITY REPORT
===========================

RAW COLLECTION
--------------
Rows:
{len(raw_df)}

Duplicate Student IDs:
{duplicate_ids}

Missing GPA:
{missing_gpa}

Missing Attendance:
{missing_attendance}

Invalid Age:
{invalid_age}

Invalid GPA:
{invalid_gpa}

Invalid Attendance:
{invalid_attendance}


CLEAN COLLECTION
----------------
Rows:
{len(clean_df)}

Missing Values:
{clean_df.isnull().sum().sum()}

Duplicate Student IDs:
{clean_df["student_id"].duplicated().sum()}


VALIDATION STATUS
-----------------
PASSED
"""

    REPORT_FILE.write_text(
        report,
        encoding="utf-8"
    )

    print(
        "\nتم إنشاء MongoDB Quality Report:"
    )

    print(
        REPORT_FILE
    )


# ==========================================================
# تشغيل MongoDB Pipeline
# ==========================================================

def main():

    print(
        "\n========== MONGODB PIPELINE START =========="
    )

    client = connect_mongodb()

    try:

        database = client[
            DATABASE_NAME
        ]

        raw_collection = database[
            RAW_COLLECTION
        ]

        # 1. فحص Raw Collection
        inspect_raw_data(
            raw_collection
        )

        # 2. Nested Query
        run_nested_query(
            raw_collection
        )

        # 3. Array Query
        run_array_query(
            raw_collection
        )

        # 4. Aggregation
        run_aggregation(
            raw_collection
        )

        # 5. استخراج البيانات
        raw_df = extract_to_dataframe(
            raw_collection
        )

        # 6. اكتشاف مشاكل الجودة
        inspect_quality(
            raw_df
        )

        # 7. تنظيف وتحويل
        clean_df = clean_data(
            raw_df
        )

        # 8. التحقق
        validate_data(
            clean_df
        )

        # 9. إعادة بناء Documents
        clean_documents = (
            dataframe_to_documents(
                clean_df
            )
        )

        # 10. حفظ Collection النظيفة
        save_clean_collection(
            database,
            clean_documents
        )

        # 11. حفظ CSV
        save_processed_csv(
            clean_df
        )

        # 12. تقرير الجودة
        create_quality_report(
            raw_df,
            clean_df
        )

    finally:

        client.close()

        print(
            "\nتم إغلاق الاتصال بـ MongoDB"
        )

    print(
        "\n========== MONGODB PIPELINE COMPLETED =========="
    )


if __name__ == "__main__":
    main()