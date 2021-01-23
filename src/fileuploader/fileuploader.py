from typing import Tuple, Optional


class FileUploader:
    def upload(self, stream) -> Optional[Tuple[str, str]]:
        """
        Upload stream data to a storage
        :param stream: stream of data
        :return: a tuple of uploaded file id and it's publicly accessible URL
        """
        pass
