"""Classes for database operations."""


from bson.objectid import ObjectId
from pymongo import MongoClient, ASCENDING, errors


HOST = 'localhost'
PORT = 27017


class Database:
    client = None
    db = None
    collection = None

    def __init__(self, collection_name = 'test_collection'):
        if Database.client is None:
            Database.client = MongoClient(HOST, PORT)
        
        if Database.client is not None:
            Database.db = Database.client.test_database
            Database.collection = Database.db[collection_name]

    def count(self, filter=None):
        if filter is None:
            return Database.collection.count_documents()
        else:
            return Database.collection.count_documents(filter)
    
    def find(self, filter, many=False):
        if not many:
            return Database.collection.find_one(filter)
        else:
            return Database.collection.find(filter)

    def get_indexes(self):
        return Database.collection.index_information()

    def index(self, key, unique):
        Database.collection.create_index([(key, ASCENDING)], unique=unique)

    def insert(self, data) -> ObjectId:
        if isinstance(data, dict):
            return Database.collection.insert_one(data).inserted_id
        elif isinstance(data, list):
            try:
                return Database.collection.insert_many(data).inserted_ids
            except errors.BulkWriteError as e:
                print(f"{e}\n\tVirhe syöttäessä tietokantaan." +
                       " Mahdollisesti uniikki indexi on jo tietokannassa.")
                return []

    def replace(self, filter, replacement, upsert=False) -> int:
        """Replace a document matching filter with replacement.
        
        If upsert is True insert the replacement if filter finds nothing.
        Return the count of modified documents.
        """
        result = Database.collection.replace_one(filter, replacement, upsert)
        return result.modified_count