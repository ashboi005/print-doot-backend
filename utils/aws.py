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

async def upload_base64_image_to_s3(base64_image: str, file_extension: str = "jpg", folder="products") -> str:
    try:
        import base64
        
        # Decode base64 string
        if "base64," in base64_image:
            base64_image = base64_image.split("base64,")[1]
        
        file_content = base64.b64decode(base64_image)
        
        if not file_content or len(file_content) == 0:
            raise Exception("Decoded base64 image is empty.")
        
        unique_filename = f"{folder}/{uuid4().hex}.{file_extension}"
        file_stream = BytesIO(file_content)
        
        # Map common file extensions to MIME types
        content_type_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "svg": "image/svg+xml",
            "bmp": "image/bmp"
        }
        
        # Get the appropriate content type or default to generic image
        content_type = content_type_map.get(file_extension.lower(), f"image/{file_extension}")
            
        await run_in_threadpool(
            s3_client.upload_fileobj,
            file_stream,
            AWS_S3_BUCKET_NAME,
            unique_filename,
            ExtraArgs={"ContentType": content_type}
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
        raise Exception(f"Base64 image upload failed: {str(e)}")
