import logging
import random

from ask_sdk_core.utils import get_account_linking_access_token
from ask_sdk_model.services import ServiceException
from ask_sdk_model.ui import LinkAccountCard, SimpleCard, AskForPermissionsConsentCard

from Benutzer import AmazonBenutzer


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

        response_builder.set_should_end_session(True)

        response_builder.speak(sprach_prompts['BENUTZER_LINKING_ANWEISUNGEN'])
        response_builder.set_card(LinkAccountCard())
    else:
        # Statisches Benutzerobjekt erzeugen (noch nicht in DB)
        benutzer = AmazonBenutzer(account_linking_token)
        speech_text = random.choice(sprach_prompts['BENUTZER_LINKED_BEGRUESSUNG']).format(benutzer.get_benutzer_namen())
        response_builder.speak(speech_text)
        account_card = SimpleCard(sprach_prompts['SKILL_NAME'], speech_text)
        response_builder.set_card(account_card)
        # Nach Berechtigungen für den genauen Standort fragen
        if not (handler_input.request_envelope.context.system.user.permissions
                and handler_input.request_envelope.context.system.user.permissions.consent_token):
            response_builder.speak('Um Interessenten zu ermöglichen deine genaue Adresse zu sehen, '
                                   'erteile mir bitte über die Alexa Companion App '
                                   'die Berechtigungen dafür.')

            standort_rechte = ['read::alexa:device:all:address']
            response_builder.set_card(AskForPermissionsConsentCard(permissions=standort_rechte))
        else:
            try:
                geraete_id = handler_input.request_envelope.context.system.device.device_id
                geraete_id_client = handler_input.service_client_factory.get_device_address_service()
                standort = geraete_id_client.get_full_address(geraete_id)
                # Standortdaten ausgeben
                logging.info(f'{standort=}')

                notwendige_standortdaten = \
                    [standort.address_line2, standort.postal_code, standort.city, standort.country_code]

                if None in notwendige_standortdaten:
                    response_builder.speak('Tut mir Leid, ich konnte in deinem Benutzerkonto keine Adresse finden.')
                else:
                    benutzer_land = 'Deutschland' if standort.country_code == 'DE' else standort.country_code
                    response_builder.speak(f'Folgende Adresse habe ich finden können: '
                                           f'{standort.address_line2}, {standort.postal_code} {standort.city}, '
                                           f'{benutzer_land}')
            except ServiceException as e:
                logging.error(f'{__name__}:Service Exception: {e}')

                response_builder.speak('Tut mir Leid, es ist ein Fehler aufgetreten. Versuche es bitte erneut')
            except Exception as e:
                raise e

    return response_builder
