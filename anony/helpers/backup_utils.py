import os
import zipfile


IMPORTANT_FILES = [
    "config.py",
    "sample.env",
    "pyproject.toml",
    "uv.lock",
    "anony.session",
    "anony.session-journal",
]

IMPORTANT_DIRS = [
    "anony",
]


def create_backup_zip(zip_name: str):
    with zipfile.ZipFile(
        zip_name,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zf:

        # File penting
        for file in IMPORTANT_FILES:
            if os.path.exists(file):
                zf.write(file)

        # Source code bot
        for folder in IMPORTANT_DIRS:
            if not os.path.isdir(folder):
                continue

            for root, _, files in os.walk(folder):
                for file in files:
                    path = os.path.join(root, file)

                    if "__pycache__" in path:
                        continue

                    if path.endswith((".pyc", ".pyo")):
                        continue

                    zf.write(path)
