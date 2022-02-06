import sys
import json
import logging

from ask_sdk_core.utils import get_supported_interfaces
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective
from apl.auskunft_apl_inhalt import get_apl_daten

logger = logging.getLogger('__name__')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def auskunft_handler(handler_input):
    """
    Informationen über die Funktionen des Skills
    """
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder

    response_builder.set_should_end_session(False)

    if get_supported_interfaces(handler_input).alexa_presentation_apl:
        response_builder.add_directive(
            RenderDocumentDirective(
                document=_lade_apl_dokument('lambda/py/apl/auskunft_apl.json'),
                datasources=get_apl_daten()
            )
        )

    return response_builder.speak(
        sprach_prompts['SKILL_INFORMATIONEN']
    ).response


def _lade_apl_dokument(dateipfad: str):
    try:
        with open(dateipfad, 'r') as json_datei:
            apl_dokument = json.load(json_datei)
    except FileNotFoundError as e:
        logger.exception(f'Alexa-Sprachbefehle konnten nicht geladen werden: {e}')
        exit()
    else:
        return json.load(apl_dokument)
