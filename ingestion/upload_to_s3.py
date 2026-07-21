import boto3
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- S3 config ---
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME       = os.getenv("AWS_BUCKET_NAME")
AWS_REGION            = os.getenv("AWS_REGION")

TODAY = datetime.utcnow().strftime("%Y-%m-%d")


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )


def upload_file(s3, local_path: str, s3_key: str):
    """Upload a single file to S3."""
    s3.upload_file(local_path, AWS_BUCKET_NAME, s3_key)
    print(f"✅ Uploaded: {s3_key}")


def upload_folder(s3, local_folder: str, s3_prefix: str):
    """Recursively upload all files in a local folder to S3."""
    for root, dirs, files in os.walk(local_folder):
        for file in files:
            local_path = os.path.join(root, file)

            # Build the S3 key (path inside the bucket)
            relative_path = os.path.relpath(local_path, local_folder)
            s3_key = f"{s3_prefix}/{relative_path}".replace("\\", "/")

            try:
                upload_file(s3, local_path, s3_key)
            except Exception as e:
                print(f"❌ Failed to upload {local_path}: {e}")


def run():
    s3 = get_s3_client()
    print(f"🚀 Uploading raw data to s3://{AWS_BUCKET_NAME}/\n")

    # Upload weather JSON files
    upload_folder(
        s3,
        local_folder=os.path.join("data", "raw", "weather"),
        s3_prefix="raw/weather"
    )

    # Upload flight JSON files
    upload_folder(
        s3,
        local_folder=os.path.join("data", "raw", "flights"),
        s3_prefix="raw/flights"
    )

    # Upload BTS CSV files
    upload_folder(
        s3,
        local_folder=os.path.join("data", "raw", "bts"),
        s3_prefix="raw/bts"
    )

    print(f"\n All raw data uploaded to S3!")


if __name__ == "__main__":
    run()