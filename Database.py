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
    def get_entwickler_namen() -> pymongo.cursor.Cursor:
        return MongoDB.get_db_instance()['entwickler_namen'].find({}, {'_id': 0})

    @staticmethod
    def get_db_instance() -> any:
        return MongoDB.db_instance

    @staticmethod
    def get_eigene_inserate(uid: str) -> pymongo.cursor.Cursor:
        # UID gets replaced by the UID of the users Amazon Account
        return MongoDB.get_db_instance()['eigene_inserate'].find({'uid': uid}, {'_id': 0, 'uid': 0})

    @staticmethod
    def benutzer_hat_einstellungen_eintrag(uid: str) -> bool:
        return (
            False if MongoDB.get_db_instance()['benutzer_einstellungen'].find_one({'uid': uid}) is None else True
        )

    @staticmethod
    def benutzer_set_umkreis(uid: str, radius: int) -> None:
        db_benutzer_einstellungen = MongoDB.get_db_instance()['benutzer_einstellungen']

        benutzer_hat_eintrag = MongoDB.benutzer_hat_einstellungen_eintrag(uid)
        if benutzer_hat_eintrag:
            db_benutzer_einstellungen.update_one({'uid': uid}, {'$set': {'radius': radius}})
        else:
            db_benutzer_einstellungen.insert_one({'uid': uid, 'radius': radius})

    @staticmethod
    def benutzer_get_umkreis(uid: str) -> int | None:
        benutzer_einstellungen = MongoDB.get_db_instance()['benutzer_einstellungen'].find_one({'uid': uid})
        if benutzer_einstellungen is None:
            return None
        else:
            return benutzer_einstellungen['radius']

