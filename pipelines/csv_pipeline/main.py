from pathlib import Path
import pandas as pd
import numpy as np


# ==========================================================
# إعداد المسارات
# ==========================================================

# تحديد المجلد الرئيسي للمشروع
BASE_DIR = Path(__file__).resolve().parents[2]

# البيانات الأصلية - لا يتم التعديل عليها
RAW_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "csv"
    / "students_raw.csv"
)

# البيانات بعد المعالجة
PROCESSED_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "csv"
    / "students_clean.csv"
)

# تقرير جودة البيانات
REPORT_FILE = (
    BASE_DIR
    / "reports"
    / "csv_quality_report.txt"
)


# ==========================================================
# 1. Extract
# استخراج البيانات
# ==========================================================

def extract_data():

    # قراءة البيانات الأصلية من CSV
    df = pd.read_csv(RAW_FILE)

    print("تم تحميل البيانات الأصلية بنجاح")

    return df


# ==========================================================
# 2. Inspect
# فحص البيانات قبل المعالجة
# ==========================================================

def inspect_data(df):

    print("\n========== فحص البيانات الأصلية ==========")

    print("\nالحجم:")
    print(df.shape)

    print("\nالقيم المفقودة:")
    print(df.isnull().sum())

    print("\nالصفوف المكررة:")
    print(df.duplicated().sum())

    print("\nالإحصائيات:")
    print(df.describe())


# ==========================================================
# 3. Transform Data Types
# تحويل أنواع البيانات
# ==========================================================

def convert_data_types(df):

    # إنشاء نسخة حتى لا نعدل البيانات الأصلية
    df = df.copy()

    # تحويل الأعمدة الرقمية إلى أرقام
    # أي قيمة غير قابلة للتحويل تصبح NaN
    numeric_columns = [
        "student_id",
        "age",
        "gpa",
        "attendance"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    return df


# ==========================================================
# 4. Clean
# تنظيف البيانات
# ==========================================================

def clean_data(df):

    # العمل على نسخة من البيانات
    df = df.copy()

    # ------------------------------------------------------
    # إزالة الصفوف المكررة بالكامل
    # ------------------------------------------------------

    df = df.drop_duplicates()

    # ------------------------------------------------------
    # إزالة تكرار رقم الطالب إن وجد
    # لأن student_id يجب أن يكون فريداً
    # ------------------------------------------------------

    df = df.drop_duplicates(
        subset=["student_id"],
        keep="first"
    )

    # ------------------------------------------------------
    # تنظيف النصوص
    # ------------------------------------------------------

    df["name"] = (
        df["name"]
        .astype("string")
        .str.strip()
    )

    df["city"] = (
        df["city"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    # ------------------------------------------------------
    # معالجة GPA
    # المدى الصحيح من 0 إلى 4
    # ------------------------------------------------------

    df.loc[
        ~df["gpa"].between(0, 4),
        "gpa"
    ] = np.nan

    # تعويض القيم المفقودة بالوسيط Median
    df["gpa"] = df["gpa"].fillna(
        df["gpa"].median()
    )

    # ------------------------------------------------------
    # معالجة العمر
    # المدى المستخدم في الملزمة 16 إلى 80
    # ------------------------------------------------------

    df.loc[
        ~df["age"].between(16, 80),
        "age"
    ] = np.nan

    # تعويض العمر غير الصحيح بالوسيط
    df["age"] = df["age"].fillna(
        df["age"].median()
    )

    # ------------------------------------------------------
    # معالجة Attendance
    # المدى الصحيح من 0 إلى 100
    # ------------------------------------------------------

    df.loc[
        ~df["attendance"].between(0, 100),
        "attendance"
    ] = np.nan

    # تعويض القيم المفقودة بالوسيط
    df["attendance"] = (
        df["attendance"]
        .fillna(
            df["attendance"].median()
        )
    )

    return df


# ==========================================================
# 5. Transform
# إنشاء خصائص جديدة
# ==========================================================

def transform_data(df):

    df = df.copy()

    # تحويل الحضور من نسبة مئوية إلى معدل من 0 إلى 1
    df["attendance_rate"] = (
        df["attendance"] / 100
    )

    # تحويل GPA إلى درجة مئوية تقريبية
    df["performance_score"] = (
        df["gpa"] / 4 * 100
    )

    # إنشاء تصنيف للطالب
    df["academic_status"] = np.where(
        (
            (df["gpa"] >= 3.5)
            &
            (df["attendance"] >= 90)
        ),
        "High Performer",
        "Regular"
    )

    return df


# ==========================================================
# 6. Validate
# التحقق من صحة البيانات بعد المعالجة
# ==========================================================

def validate_data(df):

    errors = []

    # التحقق من عدم تكرار student_id
    if df["student_id"].duplicated().any():

        errors.append(
            "يوجد تكرار في student_id"
        )

    # التحقق من عدم وجود student_id مفقود
    if df["student_id"].isnull().any():

        errors.append(
            "يوجد student_id مفقود"
        )

    # التحقق من الاسم
    if df["name"].isnull().any():

        errors.append(
            "يوجد اسم طالب مفقود"
        )

    # التحقق من العمر
    if not df["age"].between(
        16,
        80
    ).all():

        errors.append(
            "يوجد عمر خارج النطاق"
        )

    # التحقق من GPA
    if not df["gpa"].between(
        0,
        4
    ).all():

        errors.append(
            "يوجد GPA خارج النطاق"
        )

    # التحقق من Attendance
    if not df["attendance"].between(
        0,
        100
    ).all():

        errors.append(
            "يوجد Attendance خارج النطاق"
        )

    # إذا وجدت أخطاء نوقف الـ Pipeline
    if errors:

        print("\nفشل التحقق من البيانات")

        for error in errors:
            print("-", error)

        raise ValueError(
            "Data validation failed"
        )

    print(
        "\nتم التحقق من البيانات بنجاح"
    )


# ==========================================================
# 7. Save
# حفظ البيانات المعالجة
# ==========================================================

def save_data(df):

    # إنشاء المجلد إذا لم يكن موجوداً
    PROCESSED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # حفظ الناتج في ملف جديد
    # لا يتم الكتابة فوق ملف Raw
    df.to_csv(
        PROCESSED_FILE,
        index=False
    )

    print(
        "\nتم حفظ البيانات المعالجة:"
    )

    print(PROCESSED_FILE)


# ==========================================================
# 8. Quality Report
# إنشاء تقرير جودة البيانات
# ==========================================================

def create_quality_report(
    raw_df,
    clean_df
):

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # حساب بعض مؤشرات جودة البيانات الأصلية
    missing_values = (
        raw_df
        .isnull()
        .sum()
        .sum()
    )

    duplicate_rows = (
        raw_df
        .duplicated()
        .sum()
    )

    invalid_age = (
        ~raw_df["age"]
        .between(16, 80)
    ).sum()

    invalid_gpa = (
        raw_df["gpa"].notna()
        &
        ~raw_df["gpa"].between(0, 4)
    ).sum()

    invalid_attendance = (
        raw_df["attendance"].notna()
        &
        ~raw_df["attendance"]
        .between(0, 100)
    ).sum()

    report = f"""
CSV DATA QUALITY REPORT
=======================

Raw Rows:
{len(raw_df)}

Processed Rows:
{len(clean_df)}

Raw Columns:
{len(raw_df.columns)}

Processed Columns:
{len(clean_df.columns)}

Missing Values Found:
{missing_values}

Duplicate Rows Found:
{duplicate_rows}

Invalid Age Values:
{invalid_age}

Invalid GPA Values:
{invalid_gpa}

Invalid Attendance Values:
{invalid_attendance}

Final Missing Values:
{clean_df.isnull().sum().sum()}

Final Duplicate Student IDs:
{clean_df["student_id"].duplicated().sum()}

Validation Status:
PASSED
"""

    REPORT_FILE.write_text(
        report,
        encoding="utf-8"
    )

    print(
        "\nتم إنشاء تقرير جودة البيانات:"
    )

    print(REPORT_FILE)


# ==========================================================
# تشغيل CSV Pipeline كاملة
# ==========================================================

def main():

    print(
        "\n========== CSV PIPELINE START =========="
    )

    # 1. Extract
    raw_df = extract_data()

    # 2. Inspect
    inspect_data(raw_df)

    # 3. Convert Types
    df = convert_data_types(raw_df)

    # 4. Clean
    df = clean_data(df)

    # 5. Transform
    df = transform_data(df)

    # 6. Validate
    validate_data(df)

    # 7. Save
    save_data(df)

    # 8. Quality Report
    create_quality_report(
        raw_df,
        df
    )

    print(
        "\n========== البيانات النهائية =========="
    )

    print(df)

    print(
        "\n========== CSV PIPELINE COMPLETED =========="
    )


if __name__ == "__main__":
    main()