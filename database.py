"""Classes for database operations."""


from bson.objectid import ObjectId
from pymongo import MongoClient, ASCENDING


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

    def insert(self, data) -> ObjectId:
        if isinstance(data, dict):
            return Database.collection.insert_one(data).inserted_id
        elif isinstance(data, list):
            return Database.collection.insert_many(data).inserted_ids
    
    def find(self, filter, many=False):
        if not many:
            return Database.collection.find_one(filter)
        else:
            return Database.collection.find(filter)

    def count(self, filter=None):
        if filter is None:
            return Database.collection.count_documents()
        else:
            return Database.collection.count_documents(filter)
    
    def index(self, key, unique):
        Database.collection.create_index([(key, ASCENDING)], unique=unique)