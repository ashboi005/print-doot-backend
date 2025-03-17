import os
from dotenv import load_dotenv
load_dotenv() 

import boto3
from uuid import uuid4
from botocore.exceptions import NoCredentialsError

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_CLOUDFRONT_URL = os.getenv("AWS_CLOUDFRONT_URL")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def upload_image_to_s3(file, folder="products"):
    try:
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{folder}/{uuid4().hex}.{file_extension}"

        s3_client.upload_fileobj(
            file.file,
            AWS_S3_BUCKET_NAME,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type}  
        )

        url = (f"{AWS_CLOUDFRONT_URL}/{unique_filename}"
               if AWS_CLOUDFRONT_URL
               else f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}")
        return url

    except NoCredentialsError:
        raise Exception("AWS credentials are invalid or not found")
