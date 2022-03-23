from itertools import islice
from typing import Any, List, Optional
from uuid import uuid5, UUID
import json

try: 
    import pymongo
except:
    pass

class LinkCacheBase:
    def __init__(self, config) -> None:
        pass
    def add_link_to_cache(self, video_link: str, vnf) -> bool:
        pass
    def get_link_from_cache(self, video_link: str) -> Optional[Any]:
        pass
    def get_links_from_cache(self, field: str, count: int, offset: int) -> List[Any]:
        pass


class MongoDBCache(LinkCacheBase):
    def __init__(self, config) -> None:
        self.client = pymongo.MongoClient(config['config']['database'], connect=False)
        table = config['config']['table']
        self.db = self.client[table]

    def add_link_to_cache(self, video_link: str, vnf):
        try:
            out = self.db.linkCache.insert_one(vnf)
            print(" ➤ [ + ] Link added to DB cache ")
            return True
        except Exception:
            print(" ➤ [ X ] Failed to add link to DB cache")
        return False

    def get_link_from_cache(self, video_link: str):
        collection = self.db.linkCache
        vnf        = collection.find_one({'tweet': video_link})
        if vnf != None: 
            hits   = ( vnf.get('hits', 0) + 1 ) 
            print(f" ➤ [ ✔ ] Link located in DB cache. hits on this link so far: [{hits}]")
            query  = { 'tweet': video_link }
            change = { "$inc" : { "hits" : 1 } }
            out    = self.db.linkCache.update_one(query, change)
            return vnf
        else:
            print(" ➤ [ X ] Link not in DB cache")

    def get_links_from_cache(self, field: str, count: int, offset: int):
        collection = self.db.linkCache
        return list(collection.find(sort = [(field, pymongo.DESCENDING )]).skip(offset).limit(count))

# This might be fine to use under local development, but once you got a huge site running or you need
# to spread the load, this local-only system will not be useful.
class JSONCache(LinkCacheBase):
    def __init__(self, config) -> None:
        self.links_cache_filename = "links.json"
        try:
            with open(self.links_cache_filename) as f:
                self.link_cache = json.load(f)
        except FileNotFoundError:
            self.link_cache = {}

    def _write_cache(self):
        with open(self.links_cache_filename, "w") as outfile: 
            json.dump(self.link_cache, outfile, indent=4, sort_keys=True)


    def add_link_to_cache(self, video_link, vnf):
        self.link_cache[video_link] = vnf
        self._write_cache()

    
    def get_link_from_cache(self, video_link):
        if video_link in self.link_cache:
            print(" ➤ [ ✔ ] Link located in json cache")
            vnf = self.link_cache[video_link]
            vnf['hits'] += 1
            self._write_cache()
            return vnf
        else:
            print(" ➤ [ X ] Link not in json cache")
            return None
    
    def get_links_from_cache(self, field: str, count: int, offset: int):
        sorted_cache = sorted(self.link_cache.values(), key=lambda l: l.get(field), reverse=True)
        return list(islice(sorted_cache, offset, offset + count))


def initialize_link_cache(link_cache_type: str, config) -> LinkCacheBase:
    if link_cache_type == "db":
        if not globals().get('pymongo'):
            raise LookupError("the pymongo library was not included during build.")
        return MongoDBCache(config)

    if link_cache_type == "json":
        return JSONCache(config)

    raise LookupError("Cache system not recognized.")
