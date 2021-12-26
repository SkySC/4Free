import sys
import requests
import logging
import json
from http.client import HTTPConnection

from ask_sdk_core.utils import get_account_linking_access_token

import Benutzer
import Database

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('__name__')
HTTPConnection.debuglevel = 1


def get_staedte_im_umkreis(land: str, plz: int, radius: int) -> list:
    """
    Städte innerhalb des Suchradius mit der geonames.org API abfragen (Limitierungen):
    - Radius <= 30km
    - 2 Credits pro findNearbyPostalCodes Anfrage
    - Login: frees@10minmail.de
    """
    url = 'http://api.geonames.org/findNearbyPostalCodesJSON'
    parameter = {
        'country': land,
        'username': 'freesfor'
    }
    # Überprüfen, ob Benutzerkonto besteht
    if Benutzer.AmazonBenutzer.benutzer_existiert():
        parameter['postalcode'] = Benutzer.AmazonBenutzer.get_benutzer_plz()
        parameter['radius'] = Database.MongoDB.benutzer_get_umkreis()
    else:
        parameter['postalcode'] = plz
        parameter['radius'] = radius

    logging.info(f'{parameter=}')
    try:
        response = requests.get(url, params=parameter)
    except requests.exceptions.RequestException as e:
        logging.exception(f'{__name__}: Städte konnten nicht abefragt werden: {e}')
        return []
    else:
        geolocation_daten = response.json()
        logging.info(json.dumps(geolocation_daten, indent=4, ensure_ascii=False))

        staedte_namen = []
        staedte_plz = []
        for geo_entry in geolocation_daten['postalCodes']:
            staedte_namen.append(geo_entry['placeName'])
            staedte_plz.append(geo_entry['postalCode'])
        # Format: [(stadt, plz), ...]
        staedte_innerhalb_radius = list(zip(staedte_namen, staedte_plz))
        logging.info(f'{staedte_innerhalb_radius=}')

    return staedte_innerhalb_radius
