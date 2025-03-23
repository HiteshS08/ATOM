import os
import tempfile
from io import BytesIO
from typing import Optional


class TempFile(object):
    _temp_file: Optional[tempfile.NamedTemporaryFile] = None
    _file_bytes: BytesIO
    _prefix: Optional[str] = None
    _extension: Optional[str] = None

    def __init__(self, file_bytes: BytesIO, prefix=None, extension: Optional[str] = None):
        self._file_bytes = file_bytes
        self._prefix = prefix
        self._extension = extension

    def __enter__(self):
        # Create a temporary file
        self._temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=self._prefix, suffix=self._extension)

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
