import logging
import random
import sys

from ask_sdk_model.dialog import ElicitSlotDirective, DelegateDirective
from ask_sdk_model import Intent, IntentConfirmationStatus, Slot, SlotConfirmationStatus

logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def detaillierte_suche_start_handler(handler_input):
    """
    Begrüßung bei detaillierter Suche <=> direkter Aufruf
    """
    attributes_manager = handler_input.attributes_manager
    response_builder = handler_input.response_builder
    request_envelope_permissions = handler_input.request_envelope.context.system.user.permissions
    sprach_prompts = attributes_manager.request_attributes['_']
    # Standortberechtigungen überprüfen
    if not (request_envelope_permissions.scopes["alexa::devices:all:geolocation:read"].status.name == 'GRANTED'
            and request_envelope_permissions.consent_token):
        return response_builder.speak(sprach_prompts['ANFRAGE_STANDORT_BERECHTIGUNGEN']).response
    # Anzahl Fragen in Session Attribut speichern
    attributes_manager.session_attributes['anzahl_verbleibende_fragen'] = 7
    response_builder.speak(str(sprach_prompts['DETAILLIERTE_SUCHE_STARTEN_BEGRUESSUNG']).format(
        attributes_manager.session_attributes['anzahl_verbleibende_fragen'])
    )

    return handler_input.response_builder.add_directive(
        DelegateDirective(updated_intent=handler_input.request_envelope.request.intent)
    ).response


def detaillierte_suche_in_progress_handler(handler_input):
    """
    Alle Fragen der normalen Suche der Reihe nach stellen
    """
    attributes_manager = handler_input.attributes_manager
    response_builder = handler_input.response_builder
    intent = handler_input.request_envelope.request.intent
    sprach_prompts = attributes_manager.request_attributes['_']
    session_attr = attributes_manager.session_attributes
    response_builder.set_should_end_session(False)

    session_attr['anzahl_verbleibende_fragen'] -= 1
    # Ändern, so dass Ton nur bei Erfolg kommt
    sprach_ausgabe = f'<speak>{sprach_prompts["FRAGE_BEANTWORTET_ERFOLG_AUDIO"]}'
    # Bezeichnung abfragen <=> nicht als Input mitgelieferts
    slots = intent.slots
    if not slots['bezeichnung'].value:
        sprach_ausgabe += f'{random.choice(sprach_prompts["ARTIKEL_BEZEICHNUNG_ERFRAGEN"])}</speak>'
        return response_builder.speak(sprach_ausgabe).add_directive(
            ElicitSlotDirective(slot_to_elicit='bezeichnung')
        ).response
    # Fortschritt ankündigen
    if session_attr['anzahl_verbleibende_fragen'] == 1:
        sprach_ausgabe += random.choice(sprach_prompts['ANZAHL_VERBLEIBENDE_FRAGEN_EINS'])
    elif session_attr['anzahl_verbleibende_fragen'] in [5, 3]:
        sprach_ausgabe += random.choice(sprach_prompts['ANZAHL_VERBLEIBENDE_FRAGEN']).format(
            session_attr['anzahl_verbleibende_fragen']
        )

    sprach_ausgabe += '</speak>'

    return response_builder.speak(sprach_ausgabe).add_directive(
        DelegateDirective(
            updated_intent=intent
        )
    ).response


def detaillierte_suche_completed_handler(handler_input):
    return handler_input.response_builder.speak("Artikel wird gesucht!").response
