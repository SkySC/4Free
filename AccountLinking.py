import logging
import random

from ask_sdk_core.utils import get_account_linking_access_token
from ask_sdk_model.ui import LinkAccountCard, SimpleCard

from Benutzer import AmazonBenutzer


def benutzer_authorisieren(handler_input):
    # Sprachstrings für deutsche Sprache laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    # Session-Token abrufen
    speech_text = ''
    soll_sitzung_enden = False
    account_linking_token = get_account_linking_access_token(handler_input)

    if account_linking_token is None:
        # Nach Account-Linking Neustart erforderlich
        logging.info('Account-Linking wird gestartet...')
        soll_sitzung_enden = True
        speech_text = sprach_prompts['BENUTZER_LINKING_ANWEISUNGEN']
        logging.info(f'{__name__:} {speech_text=}')
        account_card = LinkAccountCard()
    else:
        # Statisches Benutzerobjekt erzeugen (noch nicht in DB)
        benutzer = AmazonBenutzer(account_linking_token)
        speech_text = random.choice(sprach_prompts['BENUTZER_LINKED_BEGRUESSUNG']).format(benutzer.get_benutzer_namen())
        account_card = SimpleCard(sprach_prompts['SKILL_NAME'], speech_text)

    return (
        handler_input.response_builder
            .speak(speech_text)
            .set_card(account_card)
            .set_should_end_session(soll_sitzung_enden)
    )
