from pathlib import Path
import subprocess
import sys


# مجلد المشروع الرئيسي
BASE_DIR = Path(__file__).resolve().parent


# ملفات الـ Pipelines
PIPELINES = [
    (
        "CSV",
        BASE_DIR
        / "pipelines"
        / "csv_pipeline"
        / "main.py"
    ),

    (
        "SQLite",
        BASE_DIR
        / "pipelines"
        / "sqlite_pipeline"
        / "main.py"
    ),

    (
        "API",
        BASE_DIR
        / "pipelines"
        / "api_pipeline"
        / "main.py"
    ),

    (
        "MongoDB Seed + CRUD",
        BASE_DIR
        / "pipelines"
        / "mongodb_pipeline"
        / "seed_data.py"
    ),

    (
        "MongoDB",
        BASE_DIR
        / "pipelines"
        / "mongodb_pipeline"
        / "main.py"
    )
]


def run_pipeline(
    name,
    file_path
):

    print(
        "\n"
        + "=" * 50
    )

    print(
        f"Running {name} Pipeline"
    )

    print(
        "=" * 50
    )

    subprocess.run(
        [
            sys.executable,
            str(file_path)
        ],
        check=True
    )


def main():

    print(
        "\nSTUDENT DATA ENGINEERING PROJECT"
    )

    for name, file_path in PIPELINES:

        run_pipeline(
            name,
            file_path
        )

    print(
        "\n"
        + "=" * 50
    )

    print(
        "All pipelines completed successfully."
    )

    print(
        "=" * 50
    )


if __name__ == "__main__":
    main()