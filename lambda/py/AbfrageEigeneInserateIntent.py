import logging

import Database


def abfrage_eigene_inserate_handler(handler_input):
    """Eigene Inserate ausgeben"""
    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    response_builder.set_should_end_session(False)

    eigene_artikel = Database.MongoDB.get_eigene_inserate()
    speech_text = ''
    artikel_match_counter = 0
    for document in eigene_artikel:
        artikel_match_counter += 1
        speech_text += f'{artikel_match_counter}. Artikel: '
        keys = list(document.keys())
        for key in keys:
            speech_text += f'{key.split("_", 1)[1]}.: {str(document[key])}'
            if key != keys[-1]:
                speech_text += ', '
            else:
                # kleine Pause zwischen dem Vorlesen der Artikel erzeugen
                speech_text += '\n'

    if artikel_match_counter == 0:
        response_builder.speak(sprach_prompts['KEINE_AKTIVEN_EIGENEN_INSERATE'])
    elif artikel_match_counter == 1:
        response_builder.speak(f'{sprach_prompts["ANZAHL_AKTIVE_EIGENE_INSERATE_EINS"]} {speech_text}')
    else:
        response_builder.speak(f'{str(sprach_prompts["ANZAHL_AKTIVE_EIGENE_INSERATE"]).format(artikel_match_counter)} '
                               f'{speech_text}')

    return response_builder.response
