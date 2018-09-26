import pymongo
from gateway.structs.struct import Struct


class DocumentWObjIdNotfound(Exception):
    pass


class Repository:
    structclass = Struct
    collection_name = None

    def __init__(self, app):
        self.app = app
        self.db = app.mongo
        self.collection = self.db[self.collection_name]

    async def find(self, specs={}):
        return await self.collection.find(specs)

    async def find_one(self, specs={}):
        result = await self.collection.find_one(specs)

        if result:
            return self.structclass(result)

    async def save(self, obj):
        if obj.id:
            result = await self.collection.replace_one(
                {"_id": obj.id}, obj.serialize()
            )

            if result.matched_count == 1:
                return obj
            else:
                raise DocumentWObjIdNotfound
        else:
            obj_data = obj.serialize()
            del obj_data['_id']

            result = await self.collection.insert_one(obj_data)
            obj.id = result.inserted_id

            return obj

    async def replace_one(self, specs, obj, upsert=False):
        replacement = obj.serialize()
        if not replacement['_id']:
            del replacement['_id']

        result = await self.collection.replace_one(
            specs, replacement, upsert=upsert
        )

        if result.upserted_id:
            obj.id = result.upserted_id

        return obj, result

    async def count(self):
        return await self.collection.count_documents({})

    async def find_max(self, field, default=None):
        result = await self.collection.find(sort=[(field, pymongo.DESCENDING)], limit=1).to_list(1)

        if len(result) == 1:
            return result[0][field]
        else:
            return default
