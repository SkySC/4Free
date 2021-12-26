import logging
import sys

from ask_sdk_model.dialog import DelegateDirective
from ask_sdk_model import Intent, IntentConfirmationStatus, Slot, SlotConfirmationStatus

logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def suchergebnisse_start_handler(handler_input):
    """
    Suchergebnisse präsentieren & Navigation zwischen Treffern ermöglichen
    """
    attributes_manager = handler_input.attributes_manager
    response_builder = handler_input.response_builder
    sprach_prompts = attributes_manager.request_attributes['_']
    session_attr = attributes_manager.session_attributes
    response_builder.set_should_end_session(False)
    # Keine Treffer aus vorheriger Suche oder bisher keine Suche ausgeführt
    if 'suchergebnisse' not in session_attr.keys():
        return response_builder.speak(sprach_prompts['SUCHE_NICHT_GESTARTET_FEHLER']).response

    return response_builder.add_directive(DelegateDirective(updated_intent=handler_input.request_envelope.intent))
    # Ersten Treffer ausgeben
    logging.info(f'{session_attr["suchergebnisse"]=}')

    sprach_ausgabe = ''
    for suchtreffer in session_attr['suchergebnisse']:
        print(suchtreffer)

    return response_builder.speak('').response


def suchergebnisse_in_progress_handler(handler_input):
    return handler_input.response_builder.speak('').response


def suchergebnisse_completed_handler(handler_input):
    return handler_input.response_builder.speak('').response
