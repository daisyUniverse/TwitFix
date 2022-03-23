from datetime import date
from typing import Any

try: 
    import pymongo
except:
    pass


class StatsBase:
    def __init__(self, config) -> None:
        pass
    def add_to_stat(self, metric: str) -> None:
        pass
    def get_stats(self, day: str) -> Any:
        pass


class MongoStats(StatsBase):
    def __init__(self, config) -> None:
        self.client = pymongo.MongoClient(config['config']['database'], connect=False)
        table = config['config']['table']
        self.db = self.client[table]

    def add_to_stat(self, metric: str):
        today = str(date.today())
        try:
            collection = self.db.stats.find_one({'date': today})
            query      = { "date" : today }
            change     = { "$inc" : { metric : 1 } }
            out        = self.db.stats.update_one(query, change)
        except:
            collection = self.db.stats.insert_one({'date': today, "embeds" : 1, "linksCached" : 1, "api" : 1, "downloads" : 1 })

    def get_stats(self, day: str):
        collection = self.db.stats.find_one({'date': day})
        return collection


class NoStats(StatsBase):
    def __init__(self, config) -> None:
        pass
    def add_to_stat(self, metric: str):
        pass
    def get_stats(self, day: str):
        return {'date': day, "embeds" : 0, "linksCached" : 0, "api" : 0, "downloads" : 0 }


def initialize_stats(stat_module: str, config) -> StatsBase:
    if stat_module == "db":
        if not globals().get('pymongo'):
            raise LookupError("the pymongo library was not included during build.")
        return MongoStats(config)

    if stat_module in ["none", "json"]:
        print(" ➤ [ X ] Stats module disabled")
        return NoStats(config)

    raise LookupError(f"Stat module not recognized. {stat_module}")
