import os
import pathlib
import shutil
from typing import Tuple

import urllib3


class StorageBase:
    def __init__(self, config) -> None:
        self.config = config
        pass

    def store_media(self, url: str) -> Tuple[bool, str]:
        """
        Download the given url for rehosting by our own system.
        """
        pass

    def retrieve_media(self, own_identifier: str):
        """
        Retrieve a cached local version of the given URL
        """
        pass


class LocalFilesystem(StorageBase):
    def __init__(self, config) -> None:
        super().__init__(config)
        self.basepath = pathlib.Path(config['config']['download_base'])


    def store_media(self, url: str):
        filename = (url.rsplit('/', 1)[-1].split('.mp4')[0] + '.mp4')

        PATH = (self.basepath / filename).resolve()
        if not PATH.is_relative_to(self.basepath):
            raise OSError("Invalid media identifier.")
        if PATH.exists() and PATH.is_file() and os.access(PATH, os.R_OK):
            print(" ➤ [[ FILE EXISTS ]]")
            return True, filename

        print(" ➤ [[ FILE DOES NOT EXIST, DOWNLOADING... ]]")
        mp4file = urllib3.request.urlopen(url)
        with PATH.open('wb') as output:
            shutil.copyfileobj(mp4file, output)
        return False, filename


    def retrieve_media(self, own_identifier: str):
        PATH = (self.basepath / own_identifier).resolve()
        if not PATH.is_relative_to(self.basepath):
            raise OSError("Invalid media identifier.")
        if PATH.exists() and PATH.is_file() and os.access(PATH, os.R_OK):
            print(f' ➤ [[ PRESENTING FILE: {own_identifier!r}, URL: https://fxtwitter.com/media/{own_identifier} ]]')
            return {"output": "file", "content": PATH} # send_file accepts a path and will handle the file from there.
        return None


class NoStorage(StorageBase):
    def store_media(self, url: str):
        return False, url
    
    def retrieve_media(self, own_identifier: str):
        return {"output": "url", "url": own_identifier}


def initialize_storage(storage_type: str, config) -> StorageBase:
    if storage_type == "local":
        return LocalFilesystem(config)

    if storage_type == "none":
        return NoStorage()
    
    raise LookupError(f"Unrecognized storage {storage_type}")
