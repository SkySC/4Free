import datetime
import logging
import sys

import pymongo.errors
from pymongo import MongoClient

import Benutzer

from FindeNahegelegeneStaedte import get_staedte_im_umkreis

logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class MongoDB:
    db_instanz = None

    def __init__(self):
        logging.info('Initialisiere Datenbankverbindung...')

        try:
            client = MongoClient(
                "mongodb+srv://admin:ubszh123@cluster0.vs42n.mongodb.net/for_free_db?retryWrites=true&w=majority"
            )
        except (pymongo.errors.ConnectionFailure, pymongo.errors.ServerSelectionTimeoutError) as e:
            logging.exception(f'Verbindung zur Datenbank konnte nicht hergestellt werden: {e}')
            raise e
        else:
            MongoDB.db_instanz = client.for_free_db

    @staticmethod
    def get_entwickler_namen() -> (str, str):
        entwickler_namen_dokument = MongoDB.get_db_instance()['entwickler_namen'].find({}, {'_id': 0})
        entwickler1, entwickler2 = entwickler_namen_dokument
        return entwickler1['name'], entwickler2['name']

    @staticmethod
    def get_db_instance() -> any:
        return MongoDB.db_instanz

    @staticmethod
    def get_eigene_inserate() -> pymongo.cursor.Cursor | None:
        return MongoDB.get_db_instance()['benutzer_inserate'].find(
            {'uid': Benutzer.AmazonBenutzer.get_benutzer_uid()},
            {'_id': 0, 'uid': 0}
        )

    @staticmethod
    def benutzer_hat_einstellungen_eintrag() -> bool:
        return (
            True if MongoDB.get_db_instance()['benutzer_einstellungen'].find_one(
                {'uid': Benutzer.AmazonBenutzer.get_benutzer_uid()}
            )
            else False
        )

    @staticmethod
    def benutzer_set_umkreis(radius: int) -> bool:
        benutzer_uid = Benutzer.AmazonBenutzer.get_benutzer_uid()
        db_benutzer_einstellungen = MongoDB.get_db_instance()['benutzer_einstellungen']

        benutzer_hat_eintrag = MongoDB.benutzer_hat_einstellungen_eintrag()
        if benutzer_hat_eintrag:
            try:
                db_benutzer_einstellungen.update_one({'uid': benutzer_uid}, {'$set': {'radius': radius}})
            except (pymongo.errors.WriteError, pymongo.errors.ConnectionFailure, pymongo.errors.NetworkTimeout) as e:
                logging.exception(f'{__name__}: Dokument konnte nicht aktuallisiert werden: {e}')
                return False
        else:
            try:
                db_benutzer_einstellungen.insert_one({'uid': benutzer_uid, 'radius': radius})
            except (pymongo.errors.WriteError, pymongo.errors.ConnectionFailure, pymongo.errors.NetworkTimeout) as e:
                logging.exception(f'{__name__}: Dokument konnte nicht geschrieben werden: {e}')
                return False

        return True

    @staticmethod
    def benutzer_get_umkreis() -> int | None:
        try:
            benutzer_einstellungen = MongoDB.get_db_instance()['benutzer_einstellungen'].find_one(
                {'uid': Benutzer.AmazonBenutzer.get_benutzer_uid()}
            )
        except (pymongo.errors.NetworkTimeout, pymongo.errors.ConnectionFailure, pymongo.errors.InvalidDocument) as e:
            logging.exception(f'{__name__}: Dokument für Benutzereinstellungen konnte nicht geladen werden: {e}')
        else:
            return benutzer_einstellungen['radius']

        return None

    @staticmethod
    def benutzer_speichere_inserat(inserat: dict) -> bool:
        benutzer = Benutzer.AmazonBenutzer
        try:
            MongoDB.get_db_instance()['benutzer_inserate'].insert_one({
                'meta_beschreibung': {
                    'erstellungs_datum': str(datetime.datetime.now()),
                    'anbieter_uid': benutzer.get_benutzer_uid(),
                    'anbieter_name': benutzer.get_benutzer_namen(),
                    'anbieter_plz': benutzer.get_benutzer_plz(),
                },
                # Artikeldaten anhängen
                **inserat
            })
        except (pymongo.errors.WriteError, pymongo.errors.ConnectionFailure, pymongo.errors.NetworkTimeout) as e:
            logging.exception(f'{__name__}: Dokument für Inserat konnte nicht geschrieben werden: {e}')
        else:
            return True

        return False

    @staticmethod
    def registriere_benutzer_geraet(device_id: str) -> bool:
        try:
            MongoDB.get_db_instance()['registrierte_geraete'].insert_one({'geraete_id': device_id})
        except (pymongo.errors.WriteError, pymongo.errors.ConnectionFailure, pymongo.errors.NetworkTimeout) as e:
            logging.exception(f'{__name__}: Dokument für Geräte-ID konnte nicht geschrieben werden: {e}')
            return False
        else:
            return True

    @staticmethod
    def skill_erststart(device_id: str) -> bool:
        return (
            False if MongoDB.get_db_instance()['registrierte_geraete'].find_one({'geraete_id': device_id}) else True
        )

    @staticmethod
    def finde_passende_artikel(slots: dict, session_attr: dict) -> list | None:
        slot_wertepaare = {key: slots[key].value for key in slots}
        logging.info(f'{slot_wertepaare=}')

        benutzer = Benutzer.AmazonBenutzer
        benutzer_land = session_attr['land']
        benutzer_plz = benutzer.get_benutzer_plz() if benutzer.benutzer_existiert() else session_attr['plz']
        radius = MongoDB.benutzer_get_umkreis() if benutzer.benutzer_existiert() else session_attr['suchradius']
        staedte_im_umkreis = get_staedte_im_umkreis(land=benutzer_land, plz=benutzer_plz, radius=radius)
        plz_im_umkreis = [plz[1] for plz in staedte_im_umkreis]

        slot_wertepaare['bezeichnung'] = {'$regex': f'.*{slot_wertepaare["bezeichnung"]}.*'}
        such_params = {**slot_wertepaare, 'anbieter_plz': {'$in': plz_im_umkreis}}
        logging.info(f'{such_params=}')

        try:
            suchtreffer_cursor = MongoDB.get_db_instance()['benutzer_inserate'].find(
                {**such_params},
                {'_id': 0, 'uid': 0}
            )
        except (pymongo.errors.InvalidDocument, pymongo.errors.CursorNotFound, pymongo.errors.NetworkTimeout) as e:
            logging.exception(f'{__name__}: Dokumente konnten nicht abgerufen werden: {e}')
            return None
        else:
            return suchtreffer_cursor
