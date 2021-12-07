from Benutzer import AmazonBenutzer


def abfrage_anmeldezeitpunkt_handler(handler_input):
    """Datum der Account-Verknüpfung ausgeben"""
    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    response_builder.set_should_end_session(False)

    linking_datum = AmazonBenutzer.benutzer_get_statistik('datum')
    if linking_datum:
        response_builder.speak(str(sprach_prompts['BENUTZER_LINKING_DATUM']).format(linking_datum))
    else:
        response_builder.speak(sprach_prompts['ALLGEMEINER_FEHLER'])

    return response_builder.response
