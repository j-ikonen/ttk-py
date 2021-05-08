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
MISSING = 'P'
MATCH = 'K'
EDITED = 'E'


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
        """Return the number of documents matching filter in database.

        Args:
        - filter (dict): Filter used to match the documents.
        Default None for all documents.
        """
        if filter is None:
            return Database.collection.count_documents()
        else:
            return Database.collection.count_documents(filter)
    
    def delete(self, obj):
        """Delete document from database.

        Args:
        - obj (dict): The object or list of objects to delete.

        Return:
        - (int) Number of deleted items.
        """
        return Database.collection.delete_one(obj).deleted_count

    def find(self, filter, many=False, page=0):
        """Find documents in database.

        Args:
        - filter (dict): Filter document used for finding a match.

        - many (bool): If True return list of results matching the filter
        instead of a single document.

        - page (int): The result page number. Limit * page determines how 
        many results will be skipped from beginning.
        
        Returns:
        - The document or list of documents.
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
        """Return a char for edited status. Return "" for None filter."""
        ecode = MISSING

        if filter is None:
            ecode = ""
        elif self.count(filter) > 0:
            ecode = MATCH
        elif self.count({'code': filter['code']}) > 0:
            ecode = EDITED

        return ecode

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
        
        Args:
        - filter (dict): Dictionary used to find the document to replace.
        - replacement (dict): The new document.
        - upsert (bool): Use insert if no match found with filter.

        Returns:
        - The count of modified documents.
        """
        result = Database.collection.replace_one(filter, replacement, upsert)
        return result.modified_count