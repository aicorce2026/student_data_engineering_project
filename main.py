from pathlib import Path
import subprocess
import sys


# ==========================================================
# تحديد المجلد الرئيسي للمشروع
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent


# ==========================================================
# تشغيل ملف Python مستقل
# ==========================================================

def run_script(title, script_path):

    print("\n" + "=" * 65)
    print(f"بدء تشغيل: {title}")
    print("=" * 65)

    try:

        # استخدام نفس Python الموجود في البيئة الافتراضية الحالية
        subprocess.run(
            [
                sys.executable,
                str(script_path)
            ],
            cwd=BASE_DIR,
            check=True
        )

        print("\n" + "-" * 65)
        print(f"اكتمل بنجاح: {title}")
        print("-" * 65)

    except subprocess.CalledProcessError:

        print("\nحدث خطأ أثناء تشغيل:")
        print(title)

        # إيقاف المشروع حتى لا نكمل على بيانات غير صحيحة
        sys.exit(1)


# ==========================================================
# تشغيل المشروع الكامل
# ==========================================================

def main():

    print(
        "\n=========================================================="
    )
    print(
        "       STUDENT DATA ENGINEERING PROJECT"
    )
    print(
        "=========================================================="
    )

    # ------------------------------------------------------
    # Pipeline 1: CSV
    # ------------------------------------------------------

    run_script(
        "CSV Pipeline",
        BASE_DIR
        / "pipelines"
        / "csv_pipeline"
        / "main.py"
    )

    # ------------------------------------------------------
    # Pipeline 2: SQLite
    # ------------------------------------------------------

    run_script(
        "SQLite Pipeline",
        BASE_DIR
        / "pipelines"
        / "sqlite_pipeline"
        / "main.py"
    )

    # ------------------------------------------------------
    # Pipeline 3: API
    # ------------------------------------------------------

    run_script(
        "API Pipeline",
        BASE_DIR
        / "pipelines"
        / "api_pipeline"
        / "main.py"
    )

    # ------------------------------------------------------
    # Pipeline 4: MongoDB
    # ------------------------------------------------------

    # أولاً نتأكد من وجود Raw Collection
    # seed_data لن يكرر البيانات إذا كانت موجودة مسبقاً
    run_script(
        "MongoDB Raw Data Seed",
        BASE_DIR
        / "pipelines"
        / "mongodb_pipeline"
        / "seed_data.py"
    )

    # بعدها نشغل Pipeline المعالجة
    run_script(
        "MongoDB Pipeline",
        BASE_DIR
        / "pipelines"
        / "mongodb_pipeline"
        / "main.py"
    )

    # ------------------------------------------------------
    # اكتمال المشروع
    # ------------------------------------------------------

    print(
        "\n=========================================================="
    )
    print(
        "جميع Data Pipelines اكتملت بنجاح"
    )
    print(
        "=========================================================="
    )

    print(
        "\nتم تنفيذ:"
    )

    print(
        "1. CSV Pipeline      ✓"
    )

    print(
        "2. SQLite Pipeline   ✓"
    )

    print(
        "3. API Pipeline      ✓"
    )

    print(
        "4. MongoDB Pipeline  ✓"
    )

    print(
        "\nراجع النتائج داخل:"
    )

    print(
        "data/processed/"
    )

    print(
        "\nوراجع تقارير الجودة داخل:"
    )

    print(
        "reports/"
    )


if __name__ == "__main__":
    main()