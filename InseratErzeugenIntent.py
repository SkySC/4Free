import logging
import random
import sys

import Database

logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def inserat_erzeugen_handler(handler_input):
    # Sprachbefehle laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    response_builder.set_should_end_session(False)

    request = handler_input.request_envelope.request
    # Fragen wurden alle beantwortet
    if request.dialog_state.name == 'COMPLETED':
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

        # abholung_satzbaustein = 'mit' if slot_wert_abholung == 'ja' else 'ohne'
        # speech_text = f'Du möchtest {slot_wert_stueckzahl} {slot_wert_artikelbezeichnung} verschenken ' \
        #              f'in der Farbe {slot_wert_farbe} ' \
        #              f'aus {slot_wert_material} ' \
        #              f'vom Hersteller {slot_wert_hersteller} ' \
        #              f'mit den Maßen {slot_wert_hoehe} mal {slot_wert_breite} mal {slot_wert_laenge} ' \
        #              f'im Zustand {slot_wert_zustand} ' \
        #              f'{abholung_satzbaustein} Möglichkeit zur Abholung ' \
        #              f'Weiterhin hast du folgende Anmerkung hinterlassen: {slot_wert_anmerkung}'

        # logging.info(speech_text)

        if Database.MongoDB.benutzer_speichere_inserat(inserat_document):
            response_builder.speak(random.choice(sprach_prompts['INSERAT_SPEICHERN_ERFOLG']))
        else:
            response_builder.speak(sprach_prompts['INSERAT_SPEICHERN_FEHLER'])

    else:
        response_builder.speak(sprach_prompts['ALLGEMEINER_FEHLER'])

    # logging.info(f'{request.intent.slots=}')

    return response_builder.response
