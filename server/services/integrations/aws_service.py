import logging
import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from collections import deque
from typing import List

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

    @abstractmethod
    def enqueue_message(self, queue_url: str, message: str) -> None:
        pass

    @abstractmethod
    def dequeue_message(self, queue_url: str, max_messages: int = 10) -> List[str]:
        pass


class FakeAWSService(AbstractAWSService):
    def __init__(self):
        self.__data_folder = tempfile.gettempdir()
        self.__queue = deque()

    def upload_to_s3(self, local_file: str, bucket: str, s3_file: str) -> None:
        dst_dir = os.path.dirname(s3_file)
        os.makedirs(os.path.join(self.__data_folder, dst_dir), exist_ok=True)
        shutil.copy(local_file, os.path.join(self.__data_folder, s3_file))

    def delete_from_s3(self, bucket: str, s3_file: str) -> None:
        os.remove(os.path.join(self.__data_folder, s3_file))

    def enqueue_message(self, queue_url: str, message: str) -> None:
        self.__queue.append(message)

    def dequeue_message(self, queue_url: str, max_messages: int = 10) -> List[str]:
        return self.__queue.popleft()


class AWSService(AbstractAWSService):
    def __init__(self):
        self.__sqs_client = boto3.client("sqs")
        self.__s3_client = boto3.client("s3")

    def upload_to_s3(self, local_file: str, bucket: str, s3_file: str) -> None:
        try:
            self.__s3_client.upload_file(local_file, bucket, s3_file, ExtraArgs={"ContentType": "image/png"})

            logger.info(f"File uploaded to S3: {s3_file}")
        except Exception as e:
            logger.exception(e)
            raise ServiceError(f"Error uploading file to S3: {e}")

    def delete_from_s3(self, bucket: str, s3_file: str) -> None:
        try:
            self.__s3_client.delete_object(Bucket=bucket, Key=s3_file)

            logger.info(f"File deleted from S3: s3://{bucket}/{s3_file}")
        except Exception as e:
            logger.exception(e)
            raise ServiceError(f"Error deleting file from S3: {e}")

    def enqueue_message(self, queue_url: str, message: str) -> None:
        try:
            self.__sqs_client.send_message(QueueUrl=queue_url, MessageBody=message)

            logger.debug(f"Message pushed to SQS: {message}")
        except Exception as e:
            logger.exception(e)
            raise ServiceError(f"Error pushing message to SQS: {e}")

    def dequeue_message(self, queue_url: str, max_messages: int = 10) -> List[str]:
        try:
            response = self.__sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=0,
                VisibilityTimeout=30,
            )

            messages = response.get("Messages", [])

            if not messages:
                return []

            results = []

            for message in messages:
                receipt_handle = message["ReceiptHandle"]
                results.append(message["Body"])
                self.__sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

            return results
        except Exception as e:
            logger.exception(e)
            raise ServiceError(f"Error receiving message from SQS: {e}")
