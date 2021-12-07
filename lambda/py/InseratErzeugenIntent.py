import datetime
import logging
import random
import sys

from ask_sdk_core.utils import get_account_linking_access_token
from ask_sdk_model.dialog import (ElicitSlotDirective, DelegateDirective)
from ask_sdk_model import (SlotConfirmationStatus, Slot)

import Database

logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def inserat_erzeugen_start_handler(handler_input):
    logging.info(f'{__name__}: Dialog gestartet')
    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    intent = handler_input.request_envelope.request.intent
    response_builder.set_should_end_session(False)
    # store counter for the remaining questions in session attribute
    handler_input.attributes_manager.session_attributes['anzahl_verbleibende_fragen'] = 12
    # Cannot create new offer if account is not linked
    if get_account_linking_access_token(handler_input):
        response_builder.speak(random.choice(sprach_prompts['INSERAT_ERZEUGEN_BEGRUESSUNG']))
    else:
        response_builder.speak(sprach_prompts['INSERAT_ERZEUGEN_BENUTZER_NICHT_LINKED'])
        return response_builder.response

    return response_builder.add_directive(
        # Redirect dialog
        DelegateDirective(
            updated_intent=intent
        )
    ).response


def inserat_erzeugen_in_progress_handler(handler_input):
    logging.info(f'{__name__}: Dialog läuft')

    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    intent = handler_input.request_envelope.request.intent
    response_builder.set_should_end_session(False)
    # Update counter for remaining questions
    handler_input.attributes_manager.session_attributes['anzahl_verbleibende_fragen'] -= 1
    remaining_questions_counter = handler_input.attributes_manager.session_attributes['anzahl_verbleibende_fragen']
    speech_text = random.choice(sprach_prompts['ANZAHL_VERBLEIBENDE_FRAGEN']).format(remaining_questions_counter)
    logging.info(f'{remaining_questions_counter=}')

    slots = intent.slots
    if slots['anmerkung'].value:
        # build custom confirmation prompt
        abholung_satzbaustein = 'mit' if slots["abholung"].value == 'ja' else 'ohne'
        speech_text = f'<speak>' \
                      f'Du möchtest {slots["stueckzahl"].value} {slots["artikelbezeichnung"].value} verschenken ' \
                      f'in der Farbe {slots["farbe"].value} ' \
                      f'aus {slots["material"].value} ' \
                      f'vom Hersteller {slots["hersteller"].value} ' \
                      f'mit den Maßen {slots["hoehe"].value} mal {slots["breite"].value} mal {slots["laenge"].value} ' \
                      f'im Zustand {slots["zustand"].value} ' \
                      f'{abholung_satzbaustein} Möglichkeit zur Abholung. ' \
                      f'Außerdem hast du folgende Anmerkung hinterlassen: {slots["anmerkung"].value}' \
                      f'<break time="1s" /></speak>'

        logging.info(speech_text)

    return response_builder.speak(speech_text).add_directive(
        # redirect to this handler again to handle next question/slot or to completed_handler after the last question
        DelegateDirective(
            updated_intent=intent
        )
    ).response


def inserat_erzeugen_completed_handler(handler_input):
    logging.info(f'{__name__}: Dialog beendet')

    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    request = handler_input.request_envelope.request
    response_builder.set_should_end_session(False)
    # Interrupt, if intent has not been confirmed yet <=> user is not linked but request has to complete anyway
    if request.intent.confirmation_status.name == 'NONE':
        response_builder.speak('Inserat wurde nicht bestätigt! Abbruch')
        return response_builder.response
    # Alle Slotwerte zwischenspeichern
    slot_wert_artikelbezeichnung = request.intent.slots['artikelbezeichnung'].value
    slot_wert_form = request.intent.slots['form'].value
    slot_wert_material = request.intent.slots['material'].value
    slot_wert_abholung = request.intent.slots['abholung'].value
    slot_wert_farbe = request.intent.slots['farbe'].value
    slot_wert_zustand = request.intent.slots['zustand'].value
    slot_wert_hersteller = request.intent.slots['hersteller'].value
    slot_wert_hoehe = request.intent.slots['hoehe'].value
    slot_wert_breite = request.intent.slots['breite'].value
    slot_wert_laenge = request.intent.slots['laenge'].value
    slot_wert_stueckzahl = request.intent.slots['stueckzahl'].value
    slot_wert_anmerkung = request.intent.slots['anmerkung'].value

    inserat_document = {
        'erstellungs_datum': str(datetime.datetime.now()),
        'artikel_bezeichnung': slot_wert_artikelbezeichnung,
        'artikel_form': slot_wert_form,
        'artikel_material': slot_wert_material,
        'artikel_abholung': slot_wert_abholung,
        'artikel_farbe': slot_wert_farbe,
        'artikel_zustand': slot_wert_zustand,
        'artikel_hersteller': slot_wert_hersteller,
        'aritkel_hoehe': float(slot_wert_hoehe),
        'artikel_breite': float(slot_wert_breite),
        'aritkel_laenge': float(slot_wert_laenge),
        'artikel_stueckzahl': int(slot_wert_stueckzahl),
        'artikel_anmerkung': slot_wert_anmerkung
    }

    if Database.MongoDB.benutzer_speichere_inserat(inserat_document):
        response_builder.speak(random.choice(sprach_prompts['INSERAT_SPEICHERN_ERFOLG']))
    else:
        response_builder.speak(sprach_prompts['INSERAT_SPEICHERN_FEHLER'])

    return response_builder.response
