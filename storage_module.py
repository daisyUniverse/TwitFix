import os
import pathlib
import shutil

import urllib3


class StorageBase:
    def __init__(self, config, stat_module) -> None:
        self.config = config
        self.stat_module = stat_module
        pass

    def store_media(self, url: str):
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
    def __init__(self, config, stat_module) -> None:
        super().__init__(config, stat_module)
        self.basepath = pathlib.Path(config['config']['download_base'])


    def store_media(self, url: str):
        filename = (url.rsplit('/', 1)[-1].split('.mp4')[0] + '.mp4')

        PATH = (self.basepath / filename).resolve()
        if not PATH.is_relative_to(self.basepath):
            raise OSError("Invalid media identifier.")
        if PATH.exists() and PATH.is_file() and os.access(PATH, os.R_OK):
            print(" ➤ [[ FILE EXISTS ]]")
        else:
            print(" ➤ [[ FILE DOES NOT EXIST, DOWNLOADING... ]]")
            self.stat_module.add_to_stat('downloads')
            mp4file = urllib3.request.urlopen(url)
            with PATH.open('wb') as output:
                shutil.copyfileobj(mp4file, output)
        return filename


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
        return url
    
    def retrieve_media(self, own_identifier: str):
        return {"output": "url", "url": own_identifier}


def initialize_storage(storage_type: str, config, stats_module) -> StorageBase:
    if storage_type == "local":
        return LocalFilesystem(config, stats_module)

    if storage_type == "none":
        return NoStorage()
    
    raise LookupError(f"Unrecognized storage {storage_type}")
