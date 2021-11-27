import Database

from Benutzer import AmazonBenutzer


def eigene_inserate_handler(handler_input):
    """Eigene Inserate ausgeben"""
    speech_text = ''
    eigene_artikel = Database.MongoDB.get_eigene_inserate(AmazonBenutzer.get_benutzer_uid())

    artikel_match_counter = 0
    for document in eigene_artikel:
        artikel_match_counter += 1
        speech_text += f'{artikel_match_counter}. Artikel: '
        keys = list(document.keys())
        for key in keys:
            speech_text += f'{key}: {str(document[key])}'
            if key != keys[-1]:
                speech_text += ', '
            else:
                # kleine Pause zwischen dem Vorlesen der Artikel erzeugen
                speech_text += '\n'

    print(speech_text)

    return handler_input.response_builder.speak(speech_text).set_should_end_session(False).response
