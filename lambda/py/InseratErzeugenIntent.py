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
    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    intent = handler_input.request_envelope.request.intent
    response_builder.set_should_end_session(False)
    # Zähler für Anzahl verbleibende Fragen in Session Attribut speichern
    handler_input.attributes_manager.session_attributes['anzahl_verbleibende_fragen'] = 12
    # Inserat kann nicht erzeugt werden, solange kein Benutzer verlinkt ist
    if get_account_linking_access_token(handler_input):
        response_builder.speak(random.choice(sprach_prompts['INSERAT_ERZEUGEN_BEGRUESSUNG']))
    else:
        response_builder.speak(sprach_prompts['INSERAT_ERZEUGEN_BENUTZER_NICHT_LINKED'])
        return response_builder.response

    return response_builder.add_directive(
        # Dialog weiterleiten
        DelegateDirective(
            updated_intent=intent
        )
    ).response


def inserat_erzeugen_in_progress_handler(handler_input):
    logging.info(f'{__name__}: Dialog läuft')

    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    intent = handler_input.request_envelope.request.intent
    response_builder.set_should_end_session(False)
    # Zähler für verbleibende Fragen aktuallisieren
    handler_input.attributes_manager.session_attributes['anzahl_verbleibende_fragen'] -= 1
    anzahl_verbleibende_fragen = handler_input.attributes_manager.session_attributes['anzahl_verbleibende_fragen']
    logging.info(f'{anzahl_verbleibende_fragen=}')
    # Audio bei gültiger Antwort
    sprach_ausgabe = f'<speak>{sprach_prompts["INSERAT_ERZEUGEN_FRAGE_BEANTWORTET_AUDIO"]}'
    # Anzahl verbleibender Fragen nur an bestimmten Stellen ausgeben
    if anzahl_verbleibende_fragen in [5, 2]:
        sprach_ausgabe += random.choice(sprach_prompts['ANZAHL_VERBLEIBENDE_FRAGEN']).format(anzahl_verbleibende_fragen)
        logging.info(f'{sprach_ausgabe=}')
    elif anzahl_verbleibende_fragen == 1:
        sprach_ausgabe += random.choice(sprach_prompts['ANZAHL_VERBLEIBENDE_FRAGEN_EINS'])
    sprach_ausgabe += '</speak>'

    slots = intent.slots
    if slots['anmerkung'].value:
        # Eigener Prompt, um Artikel zu bestätigen
        abholung_satzbaustein = 'mit' if slots['abholung'].value == 'ja' else 'ohne'
        sprach_ausgabe = str(sprach_prompts['INSERAT_ERZEUGEN_ZUSAMMENFASSUNG']).format(
            slots['stueckzahl'].value,
            slots['artikelbezeichnung'].value,
            slots['farbe'].value,
            slots['material'].value,
            slots['hersteller'].value,
            slots['laenge'].value,
            slots['breite'].value,
            slots['hoehe'].value,
            slots['zustand'].value,
            abholung_satzbaustein,
            slots['anmerkung'].value
        )

        logging.info(sprach_ausgabe)

    return response_builder.speak(sprach_ausgabe).add_directive(
        # Handler erneut aufrufen, solange letzte Frage nicht erreicht, sonst inserat_erzeugen_completed_handler
        DelegateDirective(
            updated_intent=intent
        )
    ).response


def inserat_erzeugen_completed_handler(handler_input):
    logging.info(f'{__name__}: Dialog beendet')

    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    request = handler_input.request_envelope.request
    response_builder.set_should_end_session(False)
    # Abbruch, wenn es keine Bestätigung gab <=> auch wenn Benutzerkonto nicht verlinkt
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

    inserat_dokument = {
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

    if Database.MongoDB.benutzer_speichere_inserat(inserat_dokument):
        response_builder.speak(
            f'<speak>'
            f'{sprach_prompts["INSERAT_SPEICHERN_ERFOLG_AUDIO"]}'
            f'{random.choice(sprach_prompts["INSERAT_SPEICHERN_ERFOLG"])}'
            f'</speak>'
        )
    else:
        response_builder.speak(sprach_prompts['INSERAT_SPEICHERN_FEHLER'])

    return response_builder.response
