# from main.libs.aws.amazon_connect import AmazonS3
import pandas as pd
from boto3 import client
from botocore.exceptions import ClientError
from decouple import config


class S3Client:
    def __init__(self):
        self.aws_access_key = config("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = config("AWS_SECRET_ACCESS_KEY")
        self.aws_bucket_region = config("AWS_BUCKET_REGION")
        self.aws_bucket_name = config("AWS_LOG_BUCKET_NAME")
        self.aws_uri = f"https://{self.aws_bucket_name}.s3.us-east-2.amazonaws.com/"

    def delete_file(self, file_path: str) -> None:
        pass

    def get_file(self, file_path: str) -> str:
        pass

    def get_presigned_url(self, file_key: str) -> str:
        file_key = str(file_key).replace("-", "")
        # try:
        s3_obj = client(
            "s3",
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
        )
        url = s3_obj.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.aws_bucket_name, "Key": file_key},
            ExpiresIn=3600,
        )
        print(url)
        return url
        # except ClientError as e:
        #     raise Exception("Error generating presigned url")


# class HandleFiles:
#     def __init__(self):
#         self.s3 = S3Client()

#     def up
