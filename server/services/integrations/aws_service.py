import logging
import os
import shutil
import tempfile
from abc import ABC, abstractmethod

import boto3

from server.services import ServiceError

logger = logging.getLogger(__name__)


class AbstractAWSService(ABC):
    @abstractmethod
    def upload_to_s3(self, local_file: str, bucket: str, s3_file: str) -> None:
        pass

    @abstractmethod
    def delete_from_s3(self, bucket: str, s3_file: str) -> None:
        pass


class FakeAWSService(AbstractAWSService):
    def __init__(self):
        self.__data_folder = tempfile.gettempdir()

    def upload_to_s3(self, local_file: str, bucket: str, s3_file: str) -> None:
        dst_dir = os.path.dirname(s3_file)
        os.makedirs(os.path.join(self.__data_folder, dst_dir), exist_ok=True)
        shutil.copy(local_file, os.path.join(self.__data_folder, s3_file))

    def delete_from_s3(self, bucket: str, s3_file: str) -> None:
        os.remove(os.path.join(self.__data_folder, s3_file))


class AWSService(AbstractAWSService):
    def upload_to_s3(self, local_file: str, bucket: str, s3_file: str) -> None:
        s3 = boto3.client("s3")

        try:
            s3.upload_file(local_file, bucket, s3_file, ExtraArgs={"ContentType": "image/png"})

            logger.info(f"File uploaded to S3: {s3_file}")
        except Exception as e:
            logger.exception(e)
            raise ServiceError(f"Error uploading file to S3: {e}")

    def delete_from_s3(self, bucket: str, s3_file: str) -> None:
        s3 = boto3.client("s3")

        try:
            s3.delete_object(Bucket=bucket, Key=s3_file)

            logger.info(f"File deleted from S3: s3://{bucket}/{s3_file}")
        except Exception as e:
            logger.exception(e)
            raise ServiceError(f"Error deleting file from S3: {e}")
