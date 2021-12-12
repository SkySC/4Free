import AccountLinking
import Benutzer


def benutzer_linking_handler(handler_input):
    """Möglichkeit Account Linking zu einem späteren Zeitpunkt durchzuführen"""
    # Sprachdaten laden
    sprach_prompt = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    response_builder.set_should_end_session(False)
    # Authentifizierungsmethode aufrufen
    benutzer_linked, response_builder = AccountLinking.benutzer_authorisieren(handler_input)
    if benutzer_linked:
        response_builder.speak(str(sprach_prompt['BENUTZER_BEREITS_LINKED'])
                               .format(Benutzer.AmazonBenutzer.get_benutzer_namen()))
    else:
        response_builder.speak(sprach_prompt['BENUTZER_LINKING_ANWEISUNGEN'])

    return response_builder.response
