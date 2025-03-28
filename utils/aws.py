import os
from dotenv import load_dotenv
load_dotenv()

import boto3
from uuid import uuid4
from botocore.exceptions import NoCredentialsError
from io import BytesIO
from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_CLOUDFRONT_URL = os.getenv("AWS_CLOUDFRONT_URL")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
)

async def upload_image_to_s3(file: UploadFile, folder="products") -> str:
    try:
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{folder}/{uuid4().hex}.{file_extension}"

        try:
            file_content = await file.read()  # Async read!
        except Exception as e:
            raise Exception(f"Failed to read file content: {str(e)}")

        if not file_content or len(file_content) == 0:
            raise Exception("Uploaded file is empty.")

        file_stream = BytesIO(file_content)

        await run_in_threadpool(
            s3_client.upload_fileobj,
            file_stream,
            AWS_S3_BUCKET_NAME,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type}
        )

        url = (
            f"{AWS_CLOUDFRONT_URL}/{unique_filename}"
            if AWS_CLOUDFRONT_URL
            else f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
        )
        return url

    except NoCredentialsError:
        raise Exception("AWS credentials are invalid or not found")
    except Exception as e:
        raise Exception(f"Image upload failed: {str(e)}")
