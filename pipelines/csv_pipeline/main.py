from pathlib import Path
import logging

import numpy as np
import pandas as pd


# ==========================================================
# إعداد المسارات
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "csv"
    / "students_raw.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "csv"
    / "students_clean.csv"
)

REPORT_FILE = (
    BASE_DIR
    / "reports"
    / "csv_quality_report.txt"
)

LOG_FILE = (
    BASE_DIR
    / "logs"
    / "csv_pipeline.log"
)


REQUIRED_COLUMNS = {
    "student_id",
    "name",
    "age",
    "gpa",
    "attendance",
    "city"
}


# ==========================================================
# Logging
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
    )
)

logger = logging.getLogger(__name__)


# ==========================================================
# قراءة البيانات
# ==========================================================

def load_data(
    file_path: Path
) -> pd.DataFrame:

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    df = pd.read_csv(
        file_path
    )

    if df.empty:
        raise ValueError(
            "Dataset is empty."
        )

    return df


# ==========================================================
# التحقق من الأعمدة
# ==========================================================

def validate_schema(
    df: pd.DataFrame
) -> None:

    missing_columns = (
        REQUIRED_COLUMNS
        - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )


# ==========================================================
# تحويل أنواع البيانات
# ==========================================================

def convert_data_types(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

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
# تنظيف البيانات
# ==========================================================

def clean_data(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    # حذف الصفوف المكررة
    df = df.drop_duplicates()

    # منع تكرار رقم الطالب
    df = df.drop_duplicates(
        subset=["student_id"],
        keep="first"
    )

    # تنظيف النصوص
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

    # القيم غير الصحيحة تصبح Missing
    df.loc[
        ~df["age"].between(16, 80),
        "age"
    ] = pd.NA

    df.loc[
        ~df["gpa"].between(0, 4),
        "gpa"
    ] = pd.NA

    df.loc[
        ~df["attendance"].between(0, 100),
        "attendance"
    ] = pd.NA

    # معالجة القيم المفقودة
    for column in [
        "age",
        "gpa",
        "attendance"
    ]:

        df[column] = (
            df[column]
            .fillna(
                df[column].median()
            )
        )

    return df


# ==========================================================
# إنشاء أعمدة جديدة
# ==========================================================

def transform(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    df["attendance_rate"] = (
        df["attendance"]
        / 100
    )

    df["performance_score"] = (
        df["gpa"]
        / 4
        * 100
    )

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
# التحقق النهائي
# ==========================================================

def validate_data(
    df: pd.DataFrame
) -> None:

    errors = []

    if df.empty:
        errors.append(
            "Dataset is empty."
        )

    if df["student_id"].isnull().any():
        errors.append(
            "student_id contains NULL."
        )

    if df["student_id"].duplicated().any():
        errors.append(
            "student_id is not unique."
        )

    if df["name"].isnull().any():
        errors.append(
            "name contains NULL."
        )

    if not df["age"].between(
        16,
        80
    ).all():
        errors.append(
            "Invalid age values."
        )

    if not df["gpa"].between(
        0,
        4
    ).all():
        errors.append(
            "Invalid GPA values."
        )

    if not df["attendance"].between(
        0,
        100
    ).all():
        errors.append(
            "Invalid attendance values."
        )

    if errors:
        raise ValueError(
            "Validation failed:\n"
            + "\n".join(errors)
        )


# ==========================================================
# حفظ البيانات
# ==========================================================

def save_data(
    df: pd.DataFrame,
    file_path: Path
) -> None:

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        file_path,
        index=False
    )


# ==========================================================
# تقرير جودة بسيط
# ==========================================================

def save_report(
    raw_df: pd.DataFrame,
    final_df: pd.DataFrame
) -> None:

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report = (
        "CSV DATA QUALITY REPORT\n"
        "=======================\n"
        f"Raw rows: {len(raw_df)}\n"
        f"Final rows: {len(final_df)}\n"
        f"Missing values before cleaning: "
        f"{raw_df.isnull().sum().sum()}\n"
        f"Duplicate rows before cleaning: "
        f"{raw_df.duplicated().sum()}\n"
        "Final validation: PASSED\n"
    )

    REPORT_FILE.write_text(
        report,
        encoding="utf-8"
    )


# ==========================================================
# تشغيل الـ Pipeline
# ==========================================================

def run_pipeline() -> None:

    try:

        logger.info(
            "CSV Pipeline started."
        )

        # Extract
        raw_df = load_data(
            RAW_FILE
        )

        # Schema Validation
        validate_schema(
            raw_df
        )

        # Type Conversion
        df = convert_data_types(
            raw_df
        )

        # Cleaning
        df = clean_data(
            df
        )

        # Transformation
        df = transform(
            df
        )

        # Final Validation
        validate_data(
            df
        )

        # Save
        save_data(
            df,
            OUTPUT_FILE
        )

        save_report(
            raw_df,
            df
        )

        logger.info(
            "CSV Pipeline completed."
        )

        print(
            "CSV Pipeline completed successfully."
        )

        print(
            f"Rows: {len(df)}"
        )

        print(
            f"Output: {OUTPUT_FILE}"
        )

    except Exception as exc:

        logger.exception(
            "CSV Pipeline failed: %s",
            exc
        )

        print(
            f"CSV Pipeline failed: {exc}"
        )

        raise


if __name__ == "__main__":
    run_pipeline()