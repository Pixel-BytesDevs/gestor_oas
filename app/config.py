import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # =========================
    # DATABASE
    # =========================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost/learning_objects_db"
    )

    # =========================
    # AWS CONFIG
    # =========================
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "learning-objects-bucket")

    # =========================
    # S3 BEHAVIOR (🔥 NUEVO)
    # =========================
    S3_USE_PRESIGNED_URL: bool = os.getenv("S3_USE_PRESIGNED_URL", "true").lower() == "true"
    S3_URL_EXPIRATION: int = int(os.getenv("S3_URL_EXPIRATION", "3600"))

    # =========================
    # S3 STRUCTURE (🔥 NUEVO)
    # =========================
    S3_BASE_FOLDER: str = os.getenv("S3_BASE_FOLDER", "learning-objects")
    S3_COMPONENTS_FOLDER: str = os.getenv("S3_COMPONENTS_FOLDER", "components")

    # =========================
    # IA
    # =========================
    HUGGINGFACE_API_TOKEN: str = os.getenv("HUGGINGFACE_API_TOKEN")


settings = Settings()