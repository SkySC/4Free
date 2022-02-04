import datetime
import logging
import sys

import pymongo.errors
from pymongo import MongoClient
from bson.objectid import ObjectId
from flatten_dict import flatten

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
    def get_eigene_inserate(sortierung: str) -> list | None:
        try:
            benutzer_uid = Benutzer.AmazonBenutzer.get_benutzer_uid()
            eigene_inserate = MongoDB.get_db_instance()['benutzer_inserate'].find(
                {'meta_beschreibung.anbieter_uid': benutzer_uid},
                {'meta_beschreibung.anbieter_uid': 0}
            )

            eigene_inserate_sortiert = None
            match sortierung:
                case 'neuste zuerst' | 'neueste zuerst' | 'älteste zuletzt':
                    eigene_inserate_sortiert = list(eigene_inserate.sort(
                        'meta_beschreibung.erstellungs_datum',
                        pymongo.DESCENDING
                    ))
                case 'neuste zuletzt' | 'neueste zuletzt' | 'älteste zuerst':
                    eigene_inserate_sortiert = list(eigene_inserate.sort(
                        'meta_beschreibung.erstellungs_datum',
                        pymongo.ASCENDING
                    ))
        except (pymongo.errors.NetworkTimeout, pymongo.errors.InvalidDocument, pymongo.errors.ConnectionFailure) as e:
            logging.exception(f'{__name__}: Dokumente konnten nicht gelesen werden: {e}')
            return None
        else:
            # ObjectId in String umwandeln <=> sonst gibt es einen Fehler
            if eigene_inserate_sortiert:
                for inserat in eigene_inserate_sortiert:
                    inserat['_id'] = str(inserat['_id'])

            return eigene_inserate_sortiert

    @staticmethod
    def zaehle_eigene_inserate() -> int | None:
        try:
            benutzer_uid = Benutzer.AmazonBenutzer.get_benutzer_uid()
            anzahl_eigene_inserate = MongoDB.get_db_instance()['benutzer_inserate'].count_documents(
                {'meta_beschreibung.anbieter_uid': benutzer_uid}
            )
        except (pymongo.errors.NetworkTimeout, pymongo.errors.InvalidDocument, pymongo.errors.ConnectionFailure) as e:
            logging.exception(f'{__name__}: Dokumente konnten nicht gelesen werden: {e}')
            return None
        else:
            return anzahl_eigene_inserate

    @staticmethod
    def entferne_eigenes_inserat(artikel_id: str) -> bool:
        try:
            benutzer_uid = Benutzer.AmazonBenutzer.get_benutzer_uid()
            res = MongoDB.get_db_instance()['benutzer_inserate'].delete_one(
                {'_id': ObjectId(artikel_id), 'meta_beschreibung.anbieter_uid': benutzer_uid}
            )
            logging.info(f'Es wurde {res.deleted_count} Dokument gelöscht')

        except (pymongo.errors.NetworkTimeout, pymongo.errors.InvalidDocument, pymongo.errors.ConnectionFailure) as e:
            logging.exception(f'{__name__}: Dokumente konnte nicht gelöscht werden: {e}')
            return False
        else:
            return True

    @staticmethod
    def benutzer_einstellungen_erzeugen() -> bool:
        benutzer_uid = Benutzer.AmazonBenutzer.get_benutzer_uid()
        try:
            MongoDB.get_db_instance()['benutzer_einstellungen'].insert_one(
                {'uid': benutzer_uid, 'radius': 15, 'favoriten': []}
            )
        except (pymongo.errors.WriteError, pymongo.errors.ConnectionFailure, pymongo.errors.NetworkTimeout) as e:
            logging.exception(f'{__name__}: Dokument konnte nicht geschrieben werden: {e}')
            return False
        else:
            return True

    @staticmethod
    def benutzer_hat_einstellungen_eintrag() -> bool:
        return (
            True if MongoDB.get_db_instance()['benutzer_einstellungen'].count_documents(
                {'uid': Benutzer.AmazonBenutzer.get_benutzer_uid()}
            ) == 1
            else False
        )

    @staticmethod
    def benutzer_set_umkreis(radius: int) -> bool:
        benutzer_uid = Benutzer.AmazonBenutzer.get_benutzer_uid()
        db_benutzer_einstellungen = MongoDB.get_db_instance()['benutzer_einstellungen']
        try:
            db_benutzer_einstellungen.update_one({'uid': benutzer_uid}, {'$set': {'radius': radius}})
        except (pymongo.errors.WriteError, pymongo.errors.ConnectionFailure, pymongo.errors.NetworkTimeout) as e:
            logging.exception(f'{__name__}: Dokument konnte nicht aktuallisiert werden: {e}')
            return False
        else:
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
            True if MongoDB.get_db_instance()['registrierte_geraete'].count_documents({'geraete_id': device_id}) == 0
            else False
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
        # Bezeichnungen, welche das Wort enthalten zulassen
        slot_wertepaare['bezeichnung'] = {'$regex': f'.*{slot_wertepaare["bezeichnung"]}.*'}
        # Suchanfrage muss wegen Verschachtelung in Punktnotation konvertiert werden
        such_params = flatten(
            {'meta_beschreibung': {'anbieter_plz': {'$in': plz_im_umkreis}}, 'artikeldaten': slot_wertepaare},
            reducer='dot',
            max_flatten_depth=2
        )
        # Kategorie entfernen, da sie in dieser Version noch nicht Teil des Inserats ist und nicht in der DB vorkommt
        such_params.pop('artikeldaten.kategorie', None)
        logging.info(f'{such_params=}')

        try:
            benutzer_inserate_collection = MongoDB.get_db_instance()['benutzer_inserate']
            # Keine passenden Artikel gefunden
            if benutzer_inserate_collection.count_documents(such_params) == 0:
                return None

            suchtreffer = list(benutzer_inserate_collection.find(
                such_params,
                {'meta_beschreibung.anbieter_uid': 0}
            ))
            # ObjectId in String umwandeln <=> sonst gibt es einen Fehler
            for treffer in suchtreffer:
                treffer['_id'] = str(treffer['_id'])

        except (pymongo.errors.InvalidDocument, pymongo.errors.CursorNotFound, pymongo.errors.NetworkTimeout) as e:
            logging.exception(f'{__name__}: Dokumente konnten nicht abgerufen werden: {e}')
            return None
        else:
            return suchtreffer

    @staticmethod
    def favorit_setzen(artikel_id: str) -> bool:
        benutzer_uid = Benutzer.AmazonBenutzer.get_benutzer_uid()
        # Überprüfen, ob Artikel bereits gemerkt
        try:
            favorit_gefunden = MongoDB.get_db_instance()['benutzer_einstellungen'].count_documents(
                {'uid': benutzer_uid, 'favoriten': artikel_id}
            )
        except (pymongo.errors.WriteError, pymongo.errors.ConnectionFailure, pymongo.errors.NetworkTimeout) as e:
            logging.exception(f'{__name__}: Dokument konnte nicht abgerufen werden: {e}')
            return False
        else:
            # Favorit existiert bereits -> nicht erneut speichern
            if favorit_gefunden == 1:
                return False

        try:
            MongoDB.get_db_instance()['benutzer_einstellungen'].update_one(
                {'uid': benutzer_uid},
                {'$push': {'favoriten': artikel_id}}
            )
        except (pymongo.errors.WriteError, pymongo.errors.ConnectionFailure, pymongo.errors.NetworkTimeout) as e:
            logging.exception(f'{__name__}: Favorit konnte nicht ins Dokument geschrieben werden: {e}')
            return False
        else:
            return True

    @staticmethod
    def favorit_entfernen(artikel_id: str) -> bool:
        try:
            benutzer_uid = Benutzer.AmazonBenutzer.get_benutzer_uid()
            MongoDB.get_db_instance()['benutzer_einstellungen'].update_one(
                {'uid': benutzer_uid},
                {'$pull': {'favoriten': artikel_id}}
            )
        except (pymongo.errors.WriteError, pymongo.errors.ConnectionFailure, pymongo.errors.NetworkTimeout) as e:
            logging.exception(f'{__name__}: Favorit konnte nicht entfernt werden: {e}')
            return False
        else:
            return True
