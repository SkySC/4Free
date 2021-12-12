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


def get_nearby_cities(handler_input) -> list | None:
    """
    Städte innerhalb des Suchradius mit der geonames.org API abfragen (Limitierungen):
    - Radius <= 30km
    - 2 Credits pro findNearbyPostalCodes Anfrage
    - Login: frees@10minmail.de
    """
    session_attr = handler_input.attributes_manager.session_attributes

    url = 'http://api.geonames.org/findNearbyPostalCodesJSON'
    parameter = {
        'country': 'DE',
        'username': 'fressfor'
    }
    # Überprüfen, ob Benutzerkonto besteht
    if get_account_linking_access_token(handler_input):
        parameter['postalcode'] = Benutzer.AmazonBenutzer.get_benutzer_plz()
        parameter['radius'] = Database.MongoDB.benutzer_get_umkreis()
    else:
        parameter['postalcode'] = 69502
        parameter['radius'] = session_attr['radius']

    try:
        response = requests.get(url, params=parameter)
    except requests.exceptions.RequestException as e:
        logging.exception(f'{__name__}: Städte konnten nicht abefragt werden: {e}')
        return None
    else:
        geolocation_daten = response.json()
        logging.info(json.dumps(geolocation_daten, indent=4, ensure_ascii=False))

        stadte_namen = []
        staedte_plz = []
        for geo_entry in geolocation_daten['postalCodes']:
            stadte_namen.append(geo_entry['placeName'])
            staedte_plz.append(geo_entry['postalCode'])

        staedte_innerhalb_radius = list(zip(stadte_namen, staedte_plz))
        logging.info(f'{staedte_innerhalb_radius=}')

    return staedte_innerhalb_radius
