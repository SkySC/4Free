import Database


def eigene_inserate_handler(handler_input):
    """Eigene Inserate ausgeben"""
    tmp_uid = 'u1234'
    speech_text = ''
    eigene_artikel = Database.MongoDB.get_eigene_inserate(tmp_uid)

    for document in eigene_artikel:
        keys = list(document.keys())
        for key in keys:
            speech_text += f'{key}: {str(document[key])}'
            if key != keys[-1]:
                speech_text += ', '

    print(speech_text)

    return handler_input.response_builder.speak(speech_text).set_should_end_session(False).response
