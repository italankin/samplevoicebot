import logging
from typing import Tuple, Optional, IO
from uuid import uuid4

from boto3 import session
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

from fileuploader.fileuploader import FileUploader

logger = logging.getLogger(__name__)


class S3FileUploader(FileUploader):
    def __init__(self, aws_session: session.Session, s3_bucket: str):
        self._s3_client = aws_session.client('s3')
        self._s3_bucket = s3_bucket

    def upload(self, stream: IO) -> Optional[Tuple[str, str]]:
        object_id = uuid4().hex
        object_name = f"{object_id}.ogg"
        try:
            self._s3_client.upload_fileobj(
                stream,
                self._s3_bucket,
                object_name,
                ExtraArgs={'ContentType': 'audio/ogg'},
                Config=TransferConfig(use_threads=False)
            )
            object_url = f'https://{self._s3_bucket}.s3.amazonaws.com/{object_name}'
            logger.debug(f"object_id={object_id}, object_url={object_url}")
            return object_id, object_url
        except ClientError as e:
            logging.error(f"Error while uploading object_id={object_id}: {e}", exc_info=e)
            return None
