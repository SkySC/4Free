import Database


def entwickler_info_handler(handler_input):
    """Namen der Entwickler ausgeben"""
    entwickler_eyssam, entwickler_saleh = Database.MongoDB.get_entwickler_namen()
    speech_text = f'For Free wurde entwickelt von {entwickler_eyssam["name"]} und {entwickler_saleh["name"]}'

    return handler_input.response_builder.speak(speech_text).set_should_end_session(False).response


#        slots = handler_input.request_envelope.request.intent.slots
#        name = slots["name"].value
#
#        nameDoc = {
#            'name': name
#        }
#
#        db.names.insert(nameDoc)
#
#        speech_text = "Der Name wurde gespeichert."
#
#        handler_input.response_builder.speak(speech_text).set_card(
#            SimpleCard("Name gespeichert", speech_text)).set_should_end_session(
#            False)
#        return handler_input.response_builder.response
