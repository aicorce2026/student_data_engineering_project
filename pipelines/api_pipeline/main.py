from pathlib import Path
import json
import logging

import pandas as pd
import requests


# ==========================================================
# الإعدادات
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

API_URL = (
    "https://jsonplaceholder.typicode.com/users"
)

RAW_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "api"
    / "users_raw.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "api"
    / "users_clean.csv"
)

REPORT_FILE = (
    BASE_DIR
    / "reports"
    / "api_quality_report.txt"
)

LOG_FILE = (
    BASE_DIR
    / "logs"
    / "api_pipeline.log"
)


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
# جلب البيانات من API
# ==========================================================

def fetch_data(
    url: str
) -> list[dict]:

    try:

        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(
            data,
            list
        ):
            raise ValueError(
                "Expected a JSON list."
            )

        return data

    except requests.RequestException as exc:

        raise RuntimeError(
            "API request failed."
        ) from exc

    except ValueError as exc:

        raise RuntimeError(
            "Invalid API response."
        ) from exc


# ==========================================================
# حفظ البيانات الخام
# ==========================================================

def save_raw_data(
    data: list[dict]
) -> None:

    RAW_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with RAW_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# ==========================================================
# تحويل البيانات
# ==========================================================

def transform(
    data: list[dict]
) -> pd.DataFrame:

    rows = []

    for item in data:

        rows.append({
            "user_id":
                item.get("id"),

            "name":
                item.get("name"),

            "username":
                item.get("username"),

            "email":
                item.get("email"),

            "city":
                (
                    item.get("address")
                    or {}
                ).get("city")
        })

    return pd.DataFrame(
        rows
    )


# ==========================================================
# التحقق من البيانات
# ==========================================================

def validate(
    df: pd.DataFrame
) -> None:

    required_columns = {
        "user_id",
        "name",
        "username",
        "email",
        "city"
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
            "Dataset is empty."
        )

    if not df["user_id"].is_unique:

        raise ValueError(
            "user_id must be unique."
        )

    if df["name"].isnull().any():

        raise ValueError(
            "Name cannot be NULL."
        )


# ==========================================================
# حفظ البيانات المعالجة
# ==========================================================

def save_processed(
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
    df: pd.DataFrame
) -> None:

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report = (
        "API DATA REPORT\n"
        "===============\n"
        f"Records: {len(df)}\n"
        f"Columns: {len(df.columns)}\n"
        f"Missing values: "
        f"{df.isnull().sum().sum()}\n"
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

    logger.info(
        "Starting API Pipeline."
    )

    data = fetch_data(
        API_URL
    )

    print(
        f"Received records: {len(data)}"
    )

    save_raw_data(
        data
    )

    df = transform(
        data
    )

    validate(
        df
    )

    save_processed(
        df
    )

    save_report(
        df
    )

    logger.info(
        "API Pipeline completed."
    )

    print(
        "\nAPI Data:"
    )

    print(
        df.head()
    )

    print(
        "\nAPI Pipeline completed successfully."
    )

    print(
        f"Rows: {len(df)}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()