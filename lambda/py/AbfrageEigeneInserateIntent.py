import logging
import sys

import Database

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('__name__')


def abfrage_eigene_inserate_handler(handler_input):
    """Eigene Inserate ausgeben"""
    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    response_builder.set_should_end_session(False)

    eigene_artikel = Database.MongoDB.get_eigene_inserate()
    sprach_ausgabe = ''
    artikel_anzahl_treffer = 0
    for dokument in eigene_artikel:
        artikel_anzahl_treffer += 1
        sprach_ausgabe += f'{artikel_anzahl_treffer}. Artikel: '
        keys = list(dokument.keys())
        for key in keys:
            sprach_ausgabe += f'{key.split("_", 1)[1]}.: {str(dokument[key])}'
            if key != keys[-1]:
                sprach_ausgabe += ', '
            else:
                # Kleine Pause zwischen dem Vorlesen der Artikel erzeugen
                sprach_ausgabe += '\n'

    if artikel_anzahl_treffer == 0:
        response_builder.speak(sprach_prompts['KEINE_AKTIVEN_EIGENEN_INSERATE'])
    elif artikel_anzahl_treffer == 1:
        response_builder.speak(f'{sprach_prompts["ANZAHL_AKTIVE_EIGENE_INSERATE_EINS"]} {sprach_ausgabe}')
    else:
        response_builder.speak(f'{str(sprach_prompts["ANZAHL_AKTIVE_EIGENE_INSERATE"]).format(artikel_anzahl_treffer)} '
                               f'{sprach_ausgabe}')

    return response_builder.response
