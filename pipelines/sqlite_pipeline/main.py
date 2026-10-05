from pathlib import Path
import sqlite3

import pandas as pd


# ==========================================================
# المسارات
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "sqlite"
    / "students_original.db"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "sqlite"
    / "student_analytics.csv"
)

REPORT_FILE = (
    BASE_DIR
    / "reports"
    / "sqlite_quality_report.txt"
)


# ==========================================================
# استعلام التحليل
# ==========================================================

QUERY = """
WITH student_scores AS
(
    SELECT
        s.student_id,
        s.full_name AS student_name,
        s.major,
        s.gpa,

        COUNT(
            DISTINCT e.course_code
        ) AS courses_count,

        ROUND(
            SUM(a.score) * 100.0
            /
            NULLIF(
                SUM(a.max_score),
                0
            ),
            2
        ) AS average_score

    FROM students s

    LEFT JOIN enrollments e
        ON s.student_id = e.student_id

    LEFT JOIN assessments a
        ON e.enrollment_id = a.enrollment_id

    GROUP BY
        s.student_id,
        s.full_name,
        s.major,
        s.gpa
),

student_level AS
(
    SELECT
        student_id,
        student_name,
        major,
        gpa,
        courses_count,
        average_score,

        CASE
            WHEN average_score >= 90
                THEN 'Excellent'

            WHEN average_score >= 80
                THEN 'Very Good'

            WHEN average_score >= 70
                THEN 'Good'

            WHEN average_score >= 60
                THEN 'Pass'

            ELSE 'Weak'
        END AS performance_level

    FROM student_scores
)

SELECT
    student_id,
    student_name,
    major,
    gpa,
    courses_count,
    average_score,
    performance_level,

    RANK() OVER (
        ORDER BY average_score DESC
    ) AS university_rank

FROM student_level

ORDER BY
    university_rank,
    student_id;
"""


# ==========================================================
# الاتصال بقاعدة البيانات
# ==========================================================

def get_connection():

    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_FILE}"
        )

    return sqlite3.connect(
        DATABASE_FILE
    )


# ==========================================================
# استخراج البيانات باستخدام SQL
# ==========================================================

def load_data(
    connection
) -> pd.DataFrame:

    return pd.read_sql_query(
        QUERY,
        connection
    )


# ==========================================================
# التحقق من البيانات
# ==========================================================

def validate_data(
    df: pd.DataFrame
) -> None:

    if df.empty:
        raise ValueError(
            "Analytical dataset is empty."
        )

    if not df["student_id"].is_unique:
        raise ValueError(
            "student_id must be unique."
        )

    if df["student_name"].isnull().any():
        raise ValueError(
            "student_name contains NULL."
        )

    if not df["average_score"].between(
        0,
        100
    ).all():
        raise ValueError(
            "Invalid average score."
        )


# ==========================================================
# حفظ النتيجة
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
    df: pd.DataFrame
) -> None:

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report = (
        "SQLITE ANALYTICS REPORT\n"
        "=======================\n"
        f"Students: {len(df)}\n"
        f"Average score: "
        f"{df['average_score'].mean():.2f}\n"
        f"Highest score: "
        f"{df['average_score'].max():.2f}\n"
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

    connection = None

    try:

        connection = get_connection()

        print(
            "Connected to SQLite."
        )

        df = load_data(
            connection
        )

        validate_data(
            df
        )

        save_data(
            df
        )

        save_report(
            df
        )

        print(
            "\nStudent Analytics:"
        )

        print(
            df
        )

        print(
            "\nSQLite Pipeline completed successfully."
        )

        print(
            f"Rows: {len(df)}"
        )

        print(
            f"Output: {OUTPUT_FILE}"
        )

    finally:

        if connection is not None:

            connection.close()


if __name__ == "__main__":
    main()