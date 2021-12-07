import logging
import sys

from ask_sdk_core.utils import get_account_linking_access_token
from ask_sdk_model.ui import LinkAccountCard, SimpleCard, AskForPermissionsConsentCard

from Benutzer import AmazonBenutzer


logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def benutzer_authorisieren(handler_input) -> (bool, any):
    """Führt das Account Linking durch"""
    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    # Session-Token abrufen
    account_linking_token = get_account_linking_access_token(handler_input)
    account_already_linked = False
    if account_linking_token is None:
        # Nach Account-Linking Neustart erforderlich
        logging.info('Account-Linking wird gestartet...')

        response_builder.set_card(LinkAccountCard())
    else:
        # Statisches Benutzerobjekt erzeugen (noch nicht in DB)
        logging.info('Benutzer ist bereits verlinkt')

        account_already_linked = True
        benutzer = AmazonBenutzer(account_linking_token)
        account_card = SimpleCard(sprach_prompts['SKILL_NAME'], f'Hallo {benutzer.get_benutzer_namen()}')
        response_builder.set_card(account_card)

    return account_already_linked, response_builder
