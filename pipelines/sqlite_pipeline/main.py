from pathlib import Path
import sqlite3
import pandas as pd


# ==========================================================
# إعداد المسارات
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# قاعدة البيانات الأصلية
DATABASE_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "sqlite"
    / "students_original.db"
)

# ملف البيانات التحليلية الناتجة
PROCESSED_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "sqlite"
    / "student_analytics.csv"
)

# تقرير جودة بيانات SQLite
REPORT_FILE = (
    BASE_DIR
    / "reports"
    / "sqlite_quality_report.txt"
)


# ==========================================================
# 1. الاتصال بقاعدة البيانات
# ==========================================================

def connect_database():

    # فتح قاعدة البيانات الأصلية بوضع القراءة فقط
    # حتى نضمن عدم تعديل البيانات الأصلية
    connection = sqlite3.connect(
        f"file:{DATABASE_FILE}?mode=ro",
        uri=True
    )

    print("تم الاتصال بقاعدة SQLite بنجاح")

    return connection


# ==========================================================
# 2. فحص الجداول
# ==========================================================

def inspect_database(connection):

    query = """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name;
    """

    tables_df = pd.read_sql_query(
        query,
        connection
    )

    tables = tables_df["name"].tolist()

    print("\n========== الجداول ==========")

    for table in tables:

        count_query = (
            f"SELECT COUNT(*) AS row_count "
            f"FROM {table};"
        )

        count_df = pd.read_sql_query(
            count_query,
            connection
        )

        print(
            f"{table}: "
            f"{count_df.loc[0, 'row_count']} سجل"
        )

    return tables


# ==========================================================
# 3. التحقق من جودة البيانات
# ==========================================================

def validate_source_data(connection):

    print(
        "\n========== التحقق من جودة البيانات =========="
    )

    errors = []

    # ------------------------------------------------------
    # التحقق من أعمار الطلاب
    # ------------------------------------------------------

    invalid_age = pd.read_sql_query(
        """
        SELECT *
        FROM students
        WHERE age < 16
           OR age > 80
           OR age IS NULL;
        """,
        connection
    )

    print(
        "أعمار غير صالحة:",
        len(invalid_age)
    )

    if not invalid_age.empty:
        errors.append(
            f"Invalid student ages: {len(invalid_age)}"
        )

    # ------------------------------------------------------
    # التحقق من GPA
    # ------------------------------------------------------

    invalid_gpa = pd.read_sql_query(
        """
        SELECT *
        FROM students
        WHERE gpa < 0
           OR gpa > 4
           OR gpa IS NULL;
        """,
        connection
    )

    print(
        "قيم GPA غير صالحة:",
        len(invalid_gpa)
    )

    if not invalid_gpa.empty:
        errors.append(
            f"Invalid GPA values: {len(invalid_gpa)}"
        )

    # ------------------------------------------------------
    # التحقق من الساعات المعتمدة
    # ------------------------------------------------------

    invalid_credit_hours = pd.read_sql_query(
        """
        SELECT *
        FROM courses
        WHERE credit_hours <= 0
           OR credit_hours IS NULL;
        """,
        connection
    )

    print(
        "Credit Hours غير صالحة:",
        len(invalid_credit_hours)
    )

    if not invalid_credit_hours.empty:
        errors.append(
            "Invalid course credit hours: "
            f"{len(invalid_credit_hours)}"
        )

    # ------------------------------------------------------
    # التحقق من درجات Assessments
    # ------------------------------------------------------

    invalid_scores = pd.read_sql_query(
        """
        SELECT *
        FROM assessments
        WHERE score < 0
           OR max_score <= 0
           OR score > max_score
           OR score IS NULL
           OR max_score IS NULL;
        """,
        connection
    )

    print(
        "درجات غير صالحة:",
        len(invalid_scores)
    )

    if not invalid_scores.empty:
        errors.append(
            f"Invalid assessment scores: {len(invalid_scores)}"
        )

    return errors


# ==========================================================
# 4. التحقق من العلاقات Foreign Keys
# ==========================================================

def validate_relationships(connection):

    print(
        "\n========== التحقق من العلاقات =========="
    )

    errors = []

    # ------------------------------------------------------
    # Enrollment بدون Student
    # ------------------------------------------------------

    orphan_students = pd.read_sql_query(
        """
        SELECT e.*
        FROM enrollments e
        LEFT JOIN students s
            ON e.student_id = s.student_id
        WHERE s.student_id IS NULL;
        """,
        connection
    )

    print(
        "Enrollments بدون Student:",
        len(orphan_students)
    )

    if not orphan_students.empty:
        errors.append(
            "Enrollments without students: "
            f"{len(orphan_students)}"
        )

    # ------------------------------------------------------
    # Enrollment بدون Course
    # ------------------------------------------------------

    orphan_courses = pd.read_sql_query(
        """
        SELECT e.*
        FROM enrollments e
        LEFT JOIN courses c
            ON e.course_code = c.course_code
        WHERE c.course_code IS NULL;
        """,
        connection
    )

    print(
        "Enrollments بدون Course:",
        len(orphan_courses)
    )

    if not orphan_courses.empty:
        errors.append(
            "Enrollments without courses: "
            f"{len(orphan_courses)}"
        )

    # ------------------------------------------------------
    # Assessment بدون Enrollment
    # ------------------------------------------------------

    orphan_assessments = pd.read_sql_query(
        """
        SELECT a.*
        FROM assessments a
        LEFT JOIN enrollments e
            ON a.enrollment_id = e.enrollment_id
        WHERE e.enrollment_id IS NULL;
        """,
        connection
    )

    print(
        "Assessments بدون Enrollment:",
        len(orphan_assessments)
    )

    if not orphan_assessments.empty:
        errors.append(
            "Assessments without enrollments: "
            f"{len(orphan_assessments)}"
        )

    # ------------------------------------------------------
    # تسجيل الطالب مرتين في نفس المقرر والفصل
    # ------------------------------------------------------

    duplicate_enrollments = pd.read_sql_query(
        """
        SELECT
            student_id,
            course_code,
            semester,
            COUNT(*) AS duplicate_count
        FROM enrollments
        GROUP BY
            student_id,
            course_code,
            semester
        HAVING COUNT(*) > 1;
        """,
        connection
    )

    print(
        "تسجيلات مكررة:",
        len(duplicate_enrollments)
    )

    if not duplicate_enrollments.empty:
        errors.append(
            "Duplicate enrollments: "
            f"{len(duplicate_enrollments)}"
        )

    return errors


# ==========================================================
# 5. إنشاء Dataset تحليلي
# JOIN + GROUP BY + CTE + CASE + RANK
# ==========================================================

def build_analytical_dataset(connection):

    print(
        "\n========== إنشاء Analytical Dataset =========="
    )

    query = """
    WITH student_statistics AS
    (
        SELECT
            s.student_id,
            s.full_name,
            s.age,
            s.major,
            s.gpa,

            COUNT(
                DISTINCT e.course_code
            ) AS courses_count,

            COUNT(
                a.assessment_id
            ) AS assessments_count,

            COALESCE(
                SUM(a.score),
                0
            ) AS total_score,

            COALESCE(
                SUM(a.max_score),
                0
            ) AS total_max_score

        FROM students s

        LEFT JOIN enrollments e
            ON s.student_id = e.student_id

        LEFT JOIN assessments a
            ON e.enrollment_id = a.enrollment_id

        GROUP BY
            s.student_id,
            s.full_name,
            s.age,
            s.major,
            s.gpa
    ),

    performance AS
    (
        SELECT
            *,

            CASE
                WHEN total_max_score > 0
                THEN ROUND(
                    total_score * 100.0
                    / total_max_score,
                    2
                )
                ELSE NULL
            END AS performance_percentage

        FROM student_statistics
    ),

    classification AS
    (
        SELECT
            *,

            CASE
                WHEN performance_percentage >= 90
                    THEN 'Excellent'

                WHEN performance_percentage >= 80
                    THEN 'Very Good'

                WHEN performance_percentage >= 70
                    THEN 'Good'

                WHEN performance_percentage >= 60
                    THEN 'Pass'

                ELSE 'Weak'
            END AS performance_level

        FROM performance
    )

    SELECT
        student_id,
        full_name,
        age,
        major,
        gpa,
        courses_count,
        assessments_count,
        total_score,
        total_max_score,
        performance_percentage,
        performance_level,

        RANK() OVER (
            ORDER BY performance_percentage DESC
        ) AS university_rank

    FROM classification

    ORDER BY
        university_rank,
        student_id;
    """

    df = pd.read_sql_query(
        query,
        connection
    )

    print(df)

    return df


# ==========================================================
# 6. التحقق من الـ Dataset النهائية
# ==========================================================

def validate_analytical_dataset(df):

    print(
        "\n========== Final Validation =========="
    )

    errors = []

    # student_id يجب أن يكون فريداً
    if df["student_id"].duplicated().any():

        errors.append(
            "student_id duplicated in analytical dataset"
        )

    # student_id لا يجب أن يكون مفقوداً
    if df["student_id"].isnull().any():

        errors.append(
            "student_id contains NULL values"
        )

    # GPA يجب أن يكون ضمن المدى
    if not df["gpa"].between(
        0,
        4
    ).all():

        errors.append(
            "Invalid GPA in analytical dataset"
        )

    # النسبة يجب أن تكون من 0 إلى 100
    valid_percentage = (
        df["performance_percentage"]
        .dropna()
        .between(0, 100)
        .all()
    )

    if not valid_percentage:

        errors.append(
            "Invalid performance percentage"
        )

    if errors:

        print("فشل التحقق النهائي")

        for error in errors:
            print("-", error)

        raise ValueError(
            "Analytical dataset validation failed"
        )

    print(
        "تم التحقق من الـ Analytical Dataset بنجاح"
    )


# ==========================================================
# 7. حفظ البيانات الناتجة
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
        "\nتم حفظ البيانات التحليلية:"
    )

    print(PROCESSED_FILE)


# ==========================================================
# 8. إنشاء تقرير جودة
# ==========================================================

def create_quality_report(
    connection,
    source_errors,
    relationship_errors,
    analytical_df
):

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    students_count = pd.read_sql_query(
        """
        SELECT COUNT(*) AS total
        FROM students;
        """,
        connection
    ).loc[0, "total"]

    courses_count = pd.read_sql_query(
        """
        SELECT COUNT(*) AS total
        FROM courses;
        """,
        connection
    ).loc[0, "total"]

    enrollments_count = pd.read_sql_query(
        """
        SELECT COUNT(*) AS total
        FROM enrollments;
        """,
        connection
    ).loc[0, "total"]

    assessments_count = pd.read_sql_query(
        """
        SELECT COUNT(*) AS total
        FROM assessments;
        """,
        connection
    ).loc[0, "total"]

    total_errors = (
        len(source_errors)
        + len(relationship_errors)
    )

    validation_status = (
        "PASSED"
        if total_errors == 0
        else "ISSUES FOUND"
    )

    report = f"""
SQLITE DATA QUALITY REPORT
==========================

SOURCE DATABASE
---------------
Students:
{students_count}

Courses:
{courses_count}

Enrollments:
{enrollments_count}

Assessments:
{assessments_count}


DATA QUALITY
------------
Source Validation Issues:
{len(source_errors)}

Relationship Issues:
{len(relationship_errors)}

Total Validation Issues:
{total_errors}


ANALYTICAL DATASET
------------------
Rows:
{len(analytical_df)}

Columns:
{len(analytical_df.columns)}

Missing Values:
{analytical_df.isnull().sum().sum()}

Duplicate Student IDs:
{analytical_df["student_id"].duplicated().sum()}


VALIDATION STATUS
-----------------
{validation_status}
"""

    REPORT_FILE.write_text(
        report,
        encoding="utf-8"
    )

    print(
        "\nتم إنشاء تقرير SQLite:"
    )

    print(REPORT_FILE)


# ==========================================================
# تشغيل SQLite Pipeline
# ==========================================================

def main():

    print(
        "\n========== SQLITE PIPELINE START =========="
    )

    connection = connect_database()

    try:

        # فحص قاعدة البيانات
        inspect_database(
            connection
        )

        # التحقق من البيانات
        source_errors = validate_source_data(
            connection
        )

        # التحقق من العلاقات
        relationship_errors = (
            validate_relationships(
                connection
            )
        )

        # إنشاء البيانات التحليلية
        analytical_df = (
            build_analytical_dataset(
                connection
            )
        )

        # التحقق النهائي
        validate_analytical_dataset(
            analytical_df
        )

        # حفظ الناتج
        save_processed_data(
            analytical_df
        )

        # إنشاء تقرير الجودة
        create_quality_report(
            connection,
            source_errors,
            relationship_errors,
            analytical_df
        )

    finally:

        connection.close()

        print(
            "\nتم إغلاق الاتصال بقاعدة البيانات"
        )

    print(
        "\n========== SQLITE PIPELINE COMPLETED =========="
    )


if __name__ == "__main__":
    main()