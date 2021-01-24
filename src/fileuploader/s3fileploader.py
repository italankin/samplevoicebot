import logging
from typing import Tuple, Optional
from uuid import uuid4

from boto3 import session
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

from bot_env import bot_env
from fileuploader.fileuploader import FileUploader

logger = logging.getLogger(__name__)


class S3FileUploader(FileUploader):
    def __init__(self, aws_session: session.Session, s3_bucket: str):
        self.__s3client__ = aws_session.client('s3')
        self.__s3_bucket__ = s3_bucket

    def upload(self, stream) -> Optional[Tuple[str, str]]:
        object_id = uuid4().hex
        object_name = f"{object_id}.{bot_env.config.output_format['ext']}"  # abcdf.mp3
        try:
            self.__s3client__.upload_fileobj(
                stream,
                self.__s3_bucket__,
                object_name,
                ExtraArgs={'ContentType': bot_env.config.output_format['mime_type']},
                Config=TransferConfig(use_threads=False)
            )
            object_url = f'https://{self.__s3_bucket__}.s3.amazonaws.com/{object_name}'
            logger.debug(f"object_id={object_id}, object_url={object_url}")
            return object_id, object_url
        except ClientError as e:
            logging.error(e)
            return None
