import logging
import sys

from ask_sdk_model.dialog import DelegateDirective
from ask_sdk_model import Intent, IntentConfirmationStatus, Slot, SlotConfirmationStatus

logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def suche_starten_handler(handler_input):
    """
    Suchprozess starten & Weiterleitung auf entweder detaillierte oder einfache Suche
    """
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    request_envelope = handler_input.request_envelope
    request_envelope_permissions = request_envelope.context.system.user.permissions
    request = request_envelope.request
    response_builder.set_should_end_session(False)
    # Standortberechtigungen überprüfen
    if not (request_envelope_permissions.scopes["alexa::devices:all:geolocation:read"].status.name == 'GRANTED'
            and request_envelope_permissions.consent_token):
        return response_builder.speak(sprach_prompts['ANFRAGE_STANDORT_BERECHTIGUNGEN']).response

    slots = request.intent.slots
    # Slots extrahieren
    gesuchter_artikel_name = slots['gesuchterArtikel'].value if slots['gesuchterArtikel'].value else None
    zu_delegierender_intent_name = 'DetaillierteSucheIntent' if slots['detaillierteSuche'].value == 'ja' \
        else 'EinfacheSucheIntent'
    logging.info(f'{__name__}: {gesuchter_artikel_name=} | {zu_delegierender_intent_name=}')

    session_attr = handler_input.attributes_manager.session_attributes
    if zu_delegierender_intent_name == 'EinfacheSucheIntent':
        # Zähler für Anzahl verbleibende Fragen für die Einfache Suche in Session Attribut speichern
        session_attr['anzahl_verbleibende_fragen'] = 3 if gesuchter_artikel_name else 4
    else:
        session_attr['anzahl_verbleibende_fragen'] = 6 if gesuchter_artikel_name else 7

    response_builder.speak(str(sprach_prompts['ARTIKEL_SUCHE_EINLEITUNG']).format(
        session_attr['anzahl_verbleibende_fragen']
    ))

    return response_builder.add_directive(
        DelegateDirective(
            updated_intent=Intent(
                # Weiterleitung zu passendem Intent
                name=zu_delegierender_intent_name,
                confirmation_status=IntentConfirmationStatus.NONE,
                slots={
                    'bezeichnung': Slot(
                        name='bezeichnung',
                        confirmation_status=SlotConfirmationStatus.NONE,
                        # Artikelname übergeben, falls ex.
                        value=gesuchter_artikel_name
                    )
                }
            )
        )
    ).response
