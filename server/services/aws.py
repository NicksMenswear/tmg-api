import logging
from abc import ABC, abstractmethod

import boto3

from server.services import ServiceError

logger = logging.getLogger(__name__)


class AbstractAWSService(ABC):
    @abstractmethod
    def upload_to_s3(self, local_file, bucket, s3_file):
        raise NotImplementedError()


class FakeAWSService(AbstractAWSService):
    def upload_to_s3(self, local_file, bucket, s3_file):
        pass


class AWSService(AbstractAWSService):
    def upload_to_s3(self, local_file, bucket, s3_file):
        s3 = boto3.client("s3")

        try:
            s3.upload_file(local_file, bucket, s3_file)

            logger.info(f"File uploaded to S3: {s3_file}")
        except Exception as e:
            logger.exception(e)
            raise ServiceError(f"Error uploading file to S3: {e}")
