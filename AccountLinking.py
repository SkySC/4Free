from ask_sdk_core.utils import get_account_linking_access_token
from ask_sdk_model.ui import LinkAccountCard, SimpleCard

from Benutzer import AmazonBenutzer


def benutzer_authorisieren(handler_input):
    # Session-Token abrufen
    speech_text = ''
    soll_sitzung_enden = False
    account_linking_token = get_account_linking_access_token(handler_input)

    if account_linking_token is None:
        # Nach Account-Linking Neustart erforderlich
        soll_sitzung_enden = True
        speech_text = 'Bitte verwende die Alexa Companion App, um deinen Amazon Benutzer mit For Free zu verknüpfen. \
                        Danach kannst du mich erneut aufrufen und es kann weitergehen.'
        account_card = LinkAccountCard()
    else:
        # Statisches Benutzerobjekt erzeugen (noch nicht in DB)
        benutzer = AmazonBenutzer(account_linking_token)
        speech_text = f'Hallo {benutzer.get_benutzer_namen()}, schön dich zu sehen.'
        account_card = SimpleCard('4Free', speech_text)

    return (
        handler_input.response_builder
            .speak(speech_text)
            .set_card(account_card)
            .set_should_end_session(soll_sitzung_enden)
            .response
    )
