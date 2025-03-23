import os
import tempfile
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Union, Optional

import httpx
import requests

from .config import settings
from .docserver import get_docserver_client


class DownloadFileTemp(object):
    _temp_file: Optional[tempfile.NamedTemporaryFile] = None
    _file_bytes: BytesIO
    _prefix: Optional[str] = None

    def __init__(self, file_bytes: BytesIO, prefix=None):
        self._file_bytes = file_bytes
        self._prefix = prefix

    def __enter__(self):
        # Create a temporary file
        self._temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=self._prefix)

        # Write the content to the temporary file
        with open(self._temp_file.name, 'wb') as f:
            f.write(self._file_bytes.getbuffer())

        return self

    @property
    def name(self):
        return self._temp_file.name

    def __exit__(self, *args):
        if self._temp_file is not None:
            os.remove(self.name)


class FileStorage(ABC):
    @staticmethod
    async def get_file_from_url(url: str) -> BytesIO:
        file_res = requests.get(url, allow_redirects=True)
        file_res.raise_for_status()
        return BytesIO(file_res.content)

    @abstractmethod
    async def upload(self, file_or_url: Union[str, BytesIO], file_name=None): ...

    @abstractmethod
    async def get_file_url(self, file_id: str) -> Optional[str]: ...


class SASFileStorage(FileStorage):
    def __init__(self, container="files", file_prefix=None, ttl=1800):
        if not settings.SAS:
            raise ValueError("SAS configuration not configured")

        self.container = container
        self.file_prefix = file_prefix
        self.ttl = ttl

    async def upload(self, file_or_url: Union[str, BytesIO], file_name=None):
        if isinstance(file_or_url, str):
            file = await self.get_file_from_url(file_or_url)
        else:
            file = file_or_url

        with DownloadFileTemp(file, prefix=self.file_prefix) as tf, httpx.Client() as client:
            file_name = file_name if file_name is not None else tf.name
            r = client.put(
                url=os.path.join(settings.SAS.BASE_URL, 'azblob', self.container, file_name),
                headers=settings.SAS.HEADER,
                timeout=None,
                content=file
            )
            r.raise_for_status()
            return file_name

    async def get_file_url(self, file_name=None):
        with httpx.Client() as client:
            r = client.get(
                url=os.path.join(settings.SAS.BASE_URL, 'azblob/getbloburi', self.container, file_name, str(self.ttl)),
                headers=settings.SAS.HEADER,
                timeout=None,
            )

            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.text


class DocserverFileStorage(FileStorage):
    def __init__(self, container="files", file_prefix=None):
        self.file_prefix = file_prefix
        self.container = container
        self.client = get_docserver_client()

    async def get_file_url(self, file_id: str) -> Optional[str]:
        file = self.client.files.get_file(file_id, fields_to_return="fileUrl")
        if file is None:
            return None
        return file["fileUrl"]

    async def upload(self, file_or_url: Union[str, BytesIO], file_name=None):
        if isinstance(file_or_url, str):
            file = await self.get_file_from_url(file_or_url)
        else:
            file = file_or_url

        with DownloadFileTemp(file, prefix=self.file_prefix) as tf:
            args = {
                "file_path": tf.name,
                "bucket": self.container,
            }
            self.client.files.upload_file(**args)
