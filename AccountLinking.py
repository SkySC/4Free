import logging
import random
import sys

from ask_sdk_core.utils import get_account_linking_access_token
from ask_sdk_model.ui import LinkAccountCard, SimpleCard

from Benutzer import AmazonBenutzer

logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def benutzer_authorisieren(handler_input) -> (bool, any):
    """Führt das Account Linking durch"""
    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    # Session-Token abrufen
    benutzer_linking_token = get_account_linking_access_token(handler_input)
    benutzer_linked = False
    if benutzer_linking_token is None:
        # Nach Account-Linking Neustart erforderlich
        logging.info('Account-Linking wird gestartet...')

        response_builder.set_card(LinkAccountCard())
    else:
        logging.info('Benutzer bereits verlinkt')

        benutzer_linked = True
        # Statisches Benutzerobjekt erzeugen
        benutzer = AmazonBenutzer(benutzer_linking_token)
        benutzer_card = SimpleCard(
            sprach_prompts['SKILL_NAME'],
            str(random.choice(sprach_prompts['BENUTZER_LINKED_BEGRUESSUNG'])).format(
                benutzer.get_benutzer_namen()
            ))
        response_builder.set_card(benutzer_card)

    return benutzer_linked, response_builder
