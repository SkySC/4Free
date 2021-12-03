import logging
import random
import sys

from ask_sdk_core.utils import get_account_linking_access_token
from ask_sdk_model.ui import LinkAccountCard, SimpleCard, AskForPermissionsConsentCard

from Benutzer import AmazonBenutzer


logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def benutzer_authorisieren(handler_input):
    response_builder = handler_input.response_builder
    response_builder.set_should_end_session(False)
    # Sprachstrings für deutsche Sprache laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    # Session-Token abrufen
    account_linking_token = get_account_linking_access_token(handler_input)

    if account_linking_token is None:
        # Nach Account-Linking Neustart erforderlich
        logging.info('Account-Linking wird gestartet...')

        response_builder.speak(sprach_prompts['BENUTZER_LINKING_ANWEISUNGEN'])
        response_builder.set_card(LinkAccountCard())
    else:
        # Statisches Benutzerobjekt erzeugen (noch nicht in DB)
        benutzer = AmazonBenutzer(account_linking_token)
        speech_text = random.choice(sprach_prompts['BENUTZER_LINKED_BEGRUESSUNG']).format(benutzer.get_benutzer_namen())
        response_builder.speak(speech_text)
        account_card = SimpleCard(sprach_prompts['SKILL_NAME'], speech_text)
        response_builder.set_card(account_card)

    return response_builder
