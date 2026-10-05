from pathlib import Path
from datetime import datetime, timezone
import json
import logging

import pandas as pd
import requests


# ==========================================================
# إعداد المسارات
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# رابط الـ API الموجود في المرجع
API_URL = "https://jsonplaceholder.typicode.com/users"

# مجلد حفظ البيانات الأصلية القادمة من الـ API
RAW_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "api"
)

# البيانات النهائية بعد المعالجة
PROCESSED_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "api"
    / "users_clean.csv"
)

# تقرير الجودة
REPORT_FILE = (
    BASE_DIR
    / "reports"
    / "api_quality_report.txt"
)

# ملف السجل
LOG_FILE = (
    BASE_DIR
    / "logs"
    / "api_pipeline.log"
)


# ==========================================================
# إعداد Logging
# ==========================================================

LOG_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
    encoding="utf-8"
)

logger = logging.getLogger(__name__)


# ==========================================================
# 1. Extract
# جلب البيانات من الـ API
# ==========================================================

def extract_data():

    logger.info(
        "بدء جلب البيانات من API"
    )

    try:

        response = requests.get(
            API_URL,
            timeout=10
        )

        print(
            "Status Code:",
            response.status_code
        )

        # إظهار خطأ إذا كانت الاستجابة غير ناجحة
        response.raise_for_status()

        # تحويل JSON إلى بيانات Python
        data = response.json()

    except requests.Timeout as exc:

        raise RuntimeError(
            "انتهى وقت انتظار الـ API"
        ) from exc

    except requests.ConnectionError as exc:

        raise RuntimeError(
            "فشل الاتصال بالـ API"
        ) from exc

    except requests.HTTPError as exc:

        raise RuntimeError(
            "حدث HTTP Error"
        ) from exc

    except ValueError as exc:

        raise RuntimeError(
            "الاستجابة ليست JSON صحيحة"
        ) from exc

    # نتأكد أن النتيجة List كما نتوقع
    if not isinstance(data, list):

        raise ValueError(
            "الـ API لم يرجع قائمة بيانات"
        )

    if not data:

        raise ValueError(
            "الـ API لم يرجع أي سجلات"
        )

    print(
        "تم استخراج",
        len(data),
        "سجلات"
    )

    logger.info(
        "تم استخراج %d سجلات",
        len(data)
    )

    return data


# ==========================================================
# 2. Preserve Raw
# حفظ البيانات الأصلية قبل أي معالجة
# ==========================================================

def save_raw_data(data):

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # إنشاء اسم مختلف لكل Snapshot
    # حتى لا نكتب فوق البيانات السابقة
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    raw_file = (
        RAW_DIR
        / f"users_raw_{timestamp}.json"
    )

    with raw_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )

    print(
        "تم حفظ Raw JSON:"
    )

    print(raw_file)

    return raw_file


# ==========================================================
# 3. Transform
# تحويل JSON المتداخل إلى DataFrame
# ==========================================================

def transform_data(data):

    # json_normalize تفرد البيانات المتداخلة
    df = pd.json_normalize(data)

    # تغيير اسم id ليكون أكثر وضوحاً
    df = df.rename(
        columns={
            "id": "user_id"
        }
    )

    # إضافة معلومات مصدر البيانات
    df["source"] = "api"

    df["source_url"] = API_URL

    df["retrieved_at"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    return df


# ==========================================================
# 4. Inspect
# فحص البيانات قبل التنظيف
# ==========================================================

def inspect_data(df):

    print(
        "\n========== API DATA INSPECTION =========="
    )

    print("\nالحجم:")
    print(df.shape)

    print("\nالأعمدة:")
    print(df.columns.tolist())

    print("\nالقيم المفقودة:")
    print(df.isnull().sum())

    print("\nالسجلات المكررة:")
    print(df.duplicated().sum())

    print("\nأول 5 سجلات:")
    print(df.head())


# ==========================================================
# 5. Clean
# تنظيف البيانات
# ==========================================================

def clean_data(df):

    # نعمل على نسخة من البيانات
    df = df.copy()

    # حذف التكرار الكامل
    df = df.drop_duplicates()

    # user_id يجب أن يكون فريداً
    df = df.drop_duplicates(
        subset=["user_id"],
        keep="first"
    )

    # تنظيف الأعمدة النصية
    text_columns = [
        "name",
        "username",
        "email",
        "phone",
        "website"
    ]

    for column in text_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    return df


# ==========================================================
# 6. Validate
# التحقق من البيانات
# ==========================================================

def validate_data(df):

    errors = []

    # التأكد أن البيانات ليست فارغة
    if df.empty:

        errors.append(
            "البيانات فارغة"
        )

    # user_id لا يجب أن يكون مفقوداً
    if df["user_id"].isnull().any():

        errors.append(
            "يوجد user_id مفقود"
        )

    # user_id يجب أن يكون فريداً
    if df["user_id"].duplicated().any():

        errors.append(
            "يوجد user_id مكرر"
        )

    # الاسم مطلوب
    if df["name"].isnull().any():

        errors.append(
            "يوجد Name مفقود"
        )

    # البريد مطلوب
    if df["email"].isnull().any():

        errors.append(
            "يوجد Email مفقود"
        )

    if errors:

        print(
            "\nفشل التحقق من بيانات API"
        )

        for error in errors:
            print("-", error)

        raise ValueError(
            "API validation failed"
        )

    print(
        "\nتم التحقق من بيانات API بنجاح"
    )


# ==========================================================
# 7. Save Processed
# حفظ البيانات النهائية
# ==========================================================

def save_processed_data(df):

    PROCESSED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

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
    raw_data,
    clean_df,
    raw_file
):

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    missing_values = (
        clean_df
        .isnull()
        .sum()
        .sum()
    )

    duplicate_ids = (
        clean_df["user_id"]
        .duplicated()
        .sum()
    )

    report = f"""
API DATA QUALITY REPORT
=======================

Source:
{API_URL}

Raw Snapshot:
{raw_file.name}

Rows Extracted:
{len(raw_data)}

Rows Processed:
{len(clean_df)}

Columns:
{len(clean_df.columns)}

Missing Values:
{missing_values}

Duplicate User IDs:
{duplicate_ids}

Status:
PASSED
"""

    REPORT_FILE.write_text(
        report,
        encoding="utf-8"
    )

    print(
        "\nتم إنشاء تقرير API:"
    )

    print(REPORT_FILE)


# ==========================================================
# تشغيل API Pipeline
# ==========================================================

def main():

    print(
        "\n========== API PIPELINE START =========="
    )

    # 1. استخراج البيانات
    raw_data = extract_data()

    # 2. حفظ نسخة Raw
    raw_file = save_raw_data(
        raw_data
    )

    # 3. تحويل البيانات
    df = transform_data(
        raw_data
    )

    # 4. فحص البيانات
    inspect_data(
        df
    )

    # 5. تنظيف البيانات
    df = clean_data(
        df
    )

    # 6. التحقق
    validate_data(
        df
    )

    # 7. حفظ البيانات
    save_processed_data(
        df
    )

    # 8. إنشاء تقرير الجودة
    create_quality_report(
        raw_data,
        df,
        raw_file
    )

    print(
        "\n========== API PIPELINE COMPLETED =========="
    )


if __name__ == "__main__":
    main()