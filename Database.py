import logging

import pymongo.errors
from pymongo import MongoClient


class MongoDB:
    db_instance = None

    def __init__(self):
        print('Initialisiere Datenbankverbindung...')
        try:
            client = MongoClient("mongodb+srv://admin:ubszh123@cluster0.vs42n.mongodb.net/for_free_db?retryWrites=true&w=majority")
        except (pymongo.errors.ConnectionFailure, pymongo.errors.ServerSelectionTimeoutError) as e:
            logging.error(f'Verbindung zur Datenbank konnte nicht hergestellt werden: {e}')
            exit()
        else:
            MongoDB.db_instance = client.for_free_db

    @staticmethod
    def get_entwickler_namen() -> dict:
        return MongoDB.get_db_instance()['entwickler_namen'].find({}, {'_id': 0})

    @staticmethod
    def get_db_instance() -> any:
        return MongoDB.db_instance

    @staticmethod
    def get_eigene_inserate(uid: str) -> dict:
        # UID gets replaced by the UID of the users Amazon Account
        return MongoDB.get_db_instance()['eigene_inserate'].find({'uid': uid}, {'_id': 0, 'uid': 0})

