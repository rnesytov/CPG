async def clear_db(app):
    db = app.mongo

    for collection in await db.list_collection_names():
        collection = db.get_collection(collection)

        await collection.delete_many({})
        await collection.drop_indexes()

    yield
