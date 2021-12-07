import logging
import sys

import requests
import Database
import datetime


# Logger einrichten für aktuelles Modul
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class AmazonBenutzer:
    uid = None
    name = None
    email = None
    plz = None

    def __init__(self, access_token):
        url = f'https://api.amazon.com/user/profile?access_token={access_token}'
        benutzer_daten = requests.get(url).json()
        # Info
        logging.info(f'{benutzer_daten=}')
        # Instanzvariablen setzen
        AmazonBenutzer.uid = benutzer_daten['user_id']
        AmazonBenutzer.name = benutzer_daten['name'].split()[0]
        AmazonBenutzer.email = benutzer_daten['email']
        AmazonBenutzer.plz = benutzer_daten['postal_code']
        # Prüfen, ob Datum bereits eingetragen wurde
        if AmazonBenutzer.benutzer_get_statistik('datum') is None:
            AmazonBenutzer.anmeldedatum_speichern()

    @staticmethod
    def anmeldedatum_speichern() -> None:
        Database.MongoDB.get_db_instance()['benutzer_statistiken'].insert_one({
            'uid': AmazonBenutzer.get_benutzer_uid(),
            'datum': str(datetime.date.today())
        })

    @staticmethod
    def benutzer_get_statistik(eintrag: str) -> any:
        benutzer_statistik = Database.MongoDB.get_db_instance()['benutzer_statistiken'].find_one({
            'uid': AmazonBenutzer.get_benutzer_uid()
        })
        if benutzer_statistik is None:
            pass
        else:
            try:
                angefragter_wert = benutzer_statistik[eintrag]
            except KeyError as e:
                logging.critical(f'{__name__}:Key existiert nicht: {e}')
            else:
                return angefragter_wert

    @staticmethod
    def get_benutzer_namen() -> str:
        return AmazonBenutzer.name

    @staticmethod
    def get_benutzer_email() -> str:
        return AmazonBenutzer.email

    @staticmethod
    def get_benutzer_uid() -> str:
        return AmazonBenutzer.uid

    @staticmethod
    def get_benutzer_land() -> str:
        pass

    @staticmethod
    def get_benutzer_plz() -> int:
        return AmazonBenutzer.plz

    @staticmethod
    def get_benutzer_phone() -> int:
        pass
