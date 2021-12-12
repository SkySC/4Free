import Database


def entwickler_info_handler(handler_input):
    """Namen der Entwickler ausgeben"""
    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    response_builder.set_should_end_session(False)

    entwickler_saleh, entwickler_eyssam = Database.MongoDB.get_entwickler_namen()

    response_builder.speak(str(sprach_prompts['ENTWICKLER_INFORMATIONEN'])
                           .format(entwickler_eyssam, entwickler_saleh))

    return response_builder.response
