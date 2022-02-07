import logging
import random
import sys

from ask_sdk_model.dialog import DelegateDirective

import Benutzer
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

    logging.info(f'{intent.slots["bezeichnung"]}=')
    # Zähler für Anzahl verbleibende Fragen in Session Attribut speichern
    handler_input.attributes_manager.session_attributes['anzahl_verbleibende_fragen'] = 11
    # Inserat kann nicht erzeugt werden, solange kein Benutzer verlinkt ist
    if Benutzer.AmazonBenutzer.benutzer_existiert():
        response_builder.speak(random.choice(sprach_prompts['INSERAT_ERZEUGEN_BEGRUESSUNG']))
        response_builder.add_directive(
            DelegateDirective(updated_intent=intent)
        )
    else:
        response_builder.speak(sprach_prompts['INSERAT_ERZEUGEN_BENUTZER_NICHT_LINKED'])

    return response_builder.response


def inserat_erzeugen_in_progress_handler(handler_input):
    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    intent = handler_input.request_envelope.request.intent
    slots = intent.slots

    response_builder.set_should_end_session(False)
    # Zähler für verbleibende Fragen aktuallisieren
    handler_input.attributes_manager.session_attributes['anzahl_verbleibende_fragen'] -= 1
    anzahl_verbleibende_fragen = handler_input.attributes_manager.session_attributes['anzahl_verbleibende_fragen']
    logging.info(f'{anzahl_verbleibende_fragen=}')

    # Audio bei gültiger Antwort
    sprach_ausgabe = f'<speak>{sprach_prompts["FRAGE_BEANTWORTET_ERFOLG_AUDIO"]}'
    # Anzahl verbleibender Fragen nur an bestimmten Stellen ausgeben
    if anzahl_verbleibende_fragen in [5, 2]:
        sprach_ausgabe += random.choice(sprach_prompts['ANZAHL_VERBLEIBENDE_FRAGEN']).format(anzahl_verbleibende_fragen)
    elif anzahl_verbleibende_fragen == 1:
        sprach_ausgabe += random.choice(sprach_prompts['ANZAHL_VERBLEIBENDE_FRAGEN_EINS'])
    sprach_ausgabe += '</speak>'
    # Wenn die letzte Frage beantwortet wird
    if slots['anmerkung'].value:
        abholung_satzbaustein = 'mit' \
            if slots['abholung'].value == 'ja' \
            else 'ohne'
        sprach_ausgabe = str(sprach_prompts['INSERAT_ERZEUGEN_ZUSAMMENFASSUNG']).format(
            slots['stueckzahl'].value,
            slots['bezeichnung'].value,
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

    return response_builder.speak(sprach_ausgabe).ask(
        random.choice(sprach_prompts['ALLGEMEINER_REPROMPT'])
    ).add_directive(
        # Handler erneut aufrufen, solange letzte Frage nicht erreicht, sonst inserat_erzeugen_completed_handler
        DelegateDirective(
            updated_intent=intent
        )
    ).response


def inserat_erzeugen_completed_handler(handler_input):
    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    intent = handler_input.request_envelope.request.intent

    response_builder.set_should_end_session(False)
    # Abbruch, wenn es keine Bestätigung gab <=> auch wenn Benutzerkonto nicht verlinkt
    if intent.confirmation_status.name == 'NONE':
        response_builder.speak('Inserat wurde nicht bestätigt! Abbruch')
        return response_builder.response
    # Alle Slotwerte zwischenspeichern
    slots = intent.slots
    slot_wert_bezeichnung = slots['bezeichnung'].value
    slot_wert_material = slots['material'].value
    slot_wert_abholung = slots['abholung'].value
    slot_wert_farbe = slots['farbe'].value
    slot_wert_zustand = slots['zustand'].value
    slot_wert_hersteller = slots['hersteller'].value
    slot_wert_hoehe = slots['hoehe'].value
    slot_wert_breite = slots['breite'].value
    slot_wert_laenge = slots['laenge'].value
    slot_wert_stueckzahl = slots['stueckzahl'].value
    slot_wert_anmerkung = slots['anmerkung'].value

    inserat_dokument = {
        # Metabeschreibung wird in benutzer_speichere_inserat() hinzugefügt
        'artikeldaten': {
            'bezeichnung': slot_wert_bezeichnung,
            'material': slot_wert_material,
            'abholung': slot_wert_abholung,
            'farbe': slot_wert_farbe,
            'zustand': slot_wert_zustand,
            'hersteller': slot_wert_hersteller,
            'hoehe': float(slot_wert_hoehe),
            'breite': float(slot_wert_breite),
            'laenge': float(slot_wert_laenge),
            'stueckzahl': int(slot_wert_stueckzahl),
            'anmerkung': slot_wert_anmerkung
        }
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
