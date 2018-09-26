import logging

from collections import OrderedDict
from pymongo import ASCENDING, DESCENDING


class Index:
    ORDER_CONSTANTS = {
        'asc': ASCENDING,
        'desc': DESCENDING
    }

    INVERSED_ORDER = {v: k for k, v in ORDER_CONSTANTS.items()}

    @classmethod
    def wrap_config_index(cls, collection_name, index):
        fields = OrderedDict({})

        for field, value in index.items():
            if field not in ('unique', 'sparse'):
                fields[field] = cls.ORDER_CONSTANTS[value]

        return cls(collection_name, fields,
                   unique=index.get('unique', False),
                   sparse=index.get('sparse', False))

    def __init__(self, collection, fields, unique=False, sparse=False):
        self.collection = collection
        self.fields = fields
        self.unique = unique
        self.sparse = sparse

    def __str__(self):
        items = ', '.join(
            [f'{item[0]}: {self.INVERSED_ORDER.get(item[1])}' for item in self.fields.items()]
        )
        result = f'Index {self.collection}: f{items}'

        if self.unique:
            result = '%s unique' % result

        if self.sparse:
            result = '%s sparse' % result

        return result

    __repr__ = __str__

    @property
    def mongo_keys(self):
        return list(self.fields.items())

    @property
    def mongo_kwargs(self):
        kwargs = {}

        if self.unique:
            kwargs['unique'] = True

        if self.sparse:
            kwargs['sparse'] = True

        return kwargs


class ManageIndexes:
    index_factory = Index

    def __init__(self, app):
        self.app = app
        self.options = self.app.config.indexes

    @property
    def logger(self):
        return logging.getLogger(self.__class__.__name__)

    def build_indexes(self):
        return [self.index_factory.wrap_config_index(collection, index)
                for collection, indexes in self.options.get('collections', {}).items()
                for index in indexes]

    async def create_index(self, index):
        collection = self.app.mongo.get_collection(index.collection)

        await collection.create_index(index.mongo_keys,
                                      **index.mongo_kwargs)

        self.logger.info(f'{index} successfully created')

    async def __call__(self):
        if not self.options.management_enabled:
            return

        indexes = self.build_indexes()

        for index in indexes:
            await self.create_index(index)
