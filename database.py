"""Classes for database operations."""


from bson.objectid import ObjectId
from pymongo import MongoClient, ASCENDING, errors


HOST = 'localhost'
PORT = 27017
DB_FIND_LIMIT = 25

EDITED_NO_MATCH = 0
EDITED_DIFF_MATCH = 1
EDITED_MATCH = 2
EDITED_CHAR = ['P', 'K', 'E']


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
    
    def find(self, filter, many=False, page=0):
        """Return a document or list of documents.
        
        Args:
            - filter (dict): Filter document used for finding a match.
            - many (bool): If True return list of results matching the filter
            instead of a single document.
            - page (int): The result page number. Limit * page determines how 
            many results will be skipped from beginning.
        """
        if not many:
            return Database.collection.find_one(filter)
        else:
            return list(Database.collection.find(
                filter,
                skip=DB_FIND_LIMIT * page,
                limit=DB_FIND_LIMIT))

    def get_indexes(self):
        return Database.collection.index_information()

    def get_edited(self, filter) -> str:
        """Return a char for edited status.
        EDITED_NO_MATCH for no mathcing document found with 'code'.
        EDITED_DIFF_MATCH for edited document found with 'code'.
        EDITED_MATCH for same document found with 'code'
        """
        print(f"Database.get_edited")
        if filter is None:
            print(f"\tReturn {EDITED_CHAR[EDITED_NO_MATCH]}\n")
            return EDITED_CHAR[EDITED_NO_MATCH]
        elif self.count(filter) > 0:
            print(f"\tReturn {EDITED_CHAR[EDITED_MATCH]}\n")
            return EDITED_CHAR[EDITED_MATCH]
        elif self.count({'code': filter['code']}) > 0:
            print(f"\tReturn {EDITED_CHAR[EDITED_DIFF_MATCH]}\n")
            return EDITED_CHAR[EDITED_DIFF_MATCH]
        print(f"\tReturn {EDITED_CHAR[EDITED_NO_MATCH]}\n")
        return EDITED_CHAR[EDITED_NO_MATCH]

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