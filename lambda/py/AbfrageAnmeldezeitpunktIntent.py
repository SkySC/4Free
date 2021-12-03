from Benutzer import AmazonBenutzer


def abfrage_anmeldezeitpunkt_handler(handler_input):
    """Datum der Account-Verknüpfung ausgeben"""
    # Sprachstrings für deutsche Sprache laden
    speech_prompts = handler_input.attributes_manager.request_attributes['_']
    speech_text = ''
    linking_datum = AmazonBenutzer.benutzer_get_statistik('datum')
    if linking_datum is None:
        speech_text = 'Es ist ein Fehler aufgetreten. Versuche es bitte erneut.'
    else:
        speech_text = str(speech_prompts['BENUTZER_LINKING_DATUM']).format(linking_datum)

    return handler_input.response_builder.speak(speech_text).set_should_end_session(False).response
