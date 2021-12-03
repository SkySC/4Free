import logging
import sys

from ask_sdk_model.services import ServiceException
from ask_sdk_model.ui import AskForPermissionsConsentCard


logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def abfrage_eigene_adresse_handler(handler_input):

    response_builder = get_aktuelle_adresse(handler_input)
    response_builder.set_should_end_session(False)

    return response_builder.response


def get_aktuelle_adresse(handler_input) -> any:
    # Sprachbefehle laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    request_envelope = handler_input.request_envelope
    request_envelope_permissions = request_envelope.context.system.user.permissions

    logging.info(f'{request_envelope_permissions.consent_token=}')
    
    if not (request_envelope_permissions.scopes["alexa::devices:all:geolocation:read"].status.name == 'GRANTED'
            and request_envelope_permissions.consent_token):
        logging.info('Benutzer hat keine Berechtigung für den Standort gesetzt')

        response_builder.speak(sprach_prompts['ANFRAGE_STANDORT_BERECHTIGUNGEN'])

        standort_rechte = ['read::alexa:device:all:address']
        response_builder.set_card(AskForPermissionsConsentCard(permissions=standort_rechte))
    else:
        try:
            geraete_id = request_envelope.context.system.device.device_id
            geraete_id_client = handler_input.service_client_factory.get_device_address_service()
            standort = geraete_id_client.get_full_address(geraete_id)
            # Standortdaten ausgeben
            logging.info(f'{standort=}')

            benutzer_land = 'Deutschland' if standort.country_code == 'DE' else standort.country_code
            notwendige_standortdaten = \
                [standort.address_line2, standort.postal_code, standort.city, benutzer_land]

            if None in notwendige_standortdaten:
                response_builder.speak(sprach_prompts['ADRESSE_NICHT_GEFUNDEN_ODER_UNVOLLSTAENDIG_FEHLER'])
            else:
                response_builder.speak(str(sprach_prompts['ADRESSE_AUSGABE']).format(*notwendige_standortdaten))
        except ServiceException as e:
            logging.error(f'{__name__}:Service Exception: {e}')

            response_builder.speak(sprach_prompts['ALLGEMEINER_FEHLER'])
        except Exception as e:
            raise e

    return response_builder
