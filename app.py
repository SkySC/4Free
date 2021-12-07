import json
import logging
import random
import sys

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import (Response, DialogState)
from ask_sdk_model.ui import SimpleCard
from flask import Flask
from flask_ask_sdk.skill_adapter import SkillAdapter

import Benutzer
import Database

# Stellt sicher, dass jeder Intent erreichbar ist
sys.path.insert(0, './lambda/py')

from EntwicklerInfoIntent import entwickler_info_handler
from AbfrageEigeneInserateIntent import abfrage_eigene_inserate_handler
from RadiusEinstellenIntent import radius_einstellen_handler
from AbfrageAnmeldezeitpunktIntent import abfrage_anmeldezeitpunkt_handler
from AbfrageEigeneAdresseIntent import abfrage_eigene_adresse_handler
from InseratErzeugenIntent import (
    inserat_erzeugen_start_handler, inserat_erzeugen_in_progress_handler, inserat_erzeugen_completed_handler
)
from BenutzerLinkingIntent import benutzer_linking_handler
from AccountLinking import benutzer_authorisieren

sb = CustomSkillBuilder(api_client=DefaultApiClient())
# Logger einrichten für aktuelles Modul
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

app = Flask(__name__)
# Create a database instance
db = Database.MongoDB()


"""
Response Handler & Intent Handler im Decorator-Style
- launch_request_handler
- help_intent_handler
- cancel_and_stop_intent_handler
- fallback_handler
- session_ended_request_handler
- all_exception_handler
"""


@sb.request_handler(can_handle_func=is_request_type('LaunchRequest'))
def launch_request_handler(handler_input) -> Response:
    """Handler for Skill launch."""
    attributes_manager = handler_input.attributes_manager
    # Sprachstrings für deutsche Sprache laden
    sprach_prompts = attributes_manager.request_attributes['_']
    # load session attributes
    session_attr = attributes_manager.session_attributes
    # Start Account Linking (can be skipped) & load user data if account is linked
    account_already_linked, response_builder = benutzer_authorisieren(handler_input)
    response_builder.set_should_end_session(False)
    # speech_output = sprach_prompts['START']
    # Check the device id to enables/disable onboarding
    device_id = handler_input.request_envelope.context.system.device.device_id
    if db.skill_is_launched_first_time(device_id):
        # onboarding process
        logging.info('Onboarding wird gestartet...')

        if db.register_client_device(device_id):
            logging.info('Gerät wurde erfolgreich registriert')

        else:
            logging.warning('Fehler bei der Registrierung des Geräts')

        # Give instructions on Account Linking if skill is the launched the first time & account not linked
        if not account_already_linked:
            response_builder.speak(sprach_prompts['BENUTZER_ONBOARDING_LINKING_ANWEISUNGEN'])

    else:
        logging.info(f'{db.skill_is_launched_first_time(device_id)=}')

        if account_already_linked:
            user_name = Benutzer.AmazonBenutzer.get_benutzer_namen()
            response_builder.speak(random.choice(sprach_prompts['BENUTZER_LINKED_BEGRUESSUNG']).format(user_name))
        else:
            response_builder.speak(random.choice(sprach_prompts['BENUTZER_BEGRUESSUNG']))

    # Store search radius in session attribute, if no account can be associated
    if not account_already_linked:
        # set default search radius of 15km
        session_attr['suchradius'] = 15
        logging.info(f'{session_attr=}')

    return response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input) -> Response:
    """Handler for Help Intent."""
    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']

    response_builder = handler_input.response_builder
    response_builder.speak(sprach_prompts['HILFESEITE_EINLEITUNG']).ask(sprach_prompts['HILFESEITE_FRAGE_PROMPT'])

    return response_builder.response


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name("AMAZON.CancelIntent")(handler_input) or
    is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input) -> Response:
    """Single handler for Cancel and Stop Intent."""
    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder

    user_name = Benutzer.AmazonBenutzer.get_benutzer_namen()
    speech_output = random.choice(sprach_prompts['BENUTZER_VERABSCHIEDEN'])\
        .format(f'{"" if user_name is None else user_name}')
    response_builder.speak(speech_output)
    response_builder.set_card(SimpleCard(speech_output))

    return response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input) -> Response:
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    response_builder.set_should_end_session(False)

    response_builder.speak(sprach_prompts['FALLBACK'])

    return response_builder.response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input) -> Response:
    """Handler for Session End."""
    # Call cancel_and_stop_intent instead
    return cancel_and_stop_intent_handler(handler_input)


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception) -> Response:
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder

    logging.error(exception, exc_info=True)
    response_builder.speak(sprach_prompts['ALLGEMEINE_EXCEPTION'])

    return response_builder.response


"""
Eigene Intent-Handler im Decorator-Style
- EntwicklerInfoIntent
- AbfrageEigeneInserateIntent
- RadiusEinstellenIntent
- AbfrageAnmeldeZeitpunktIntent
- AbfrageEigeneAdresseIntent
- InseratErzeugenIntent
"""


@sb.request_handler(can_handle_func=is_intent_name('EntwicklerInfoIntent'))
def entwickler_info_handler_wrapper(handler_input) -> Response:
    return entwickler_info_handler(handler_input)


@sb.request_handler(can_handle_func=is_intent_name('AbfrageEigeneInserateIntent'))
def abfrage_eigene_inserate_handler_wrapper(handler_input) -> Response:
    return abfrage_eigene_inserate_handler(handler_input)


@sb.request_handler(can_handle_func=is_intent_name('RadiusEinstellenIntent'))
def radius_einstellen_handler_wrapper(handler_input) -> Response:
    return radius_einstellen_handler(handler_input)


@sb.request_handler(can_handle_func=is_intent_name('AbfrageAnmeldezeitpunktIntent'))
def abfrage_anmeldezeitpunkt_handler_wrapper(handler_input) -> Response:
    return abfrage_anmeldezeitpunkt_handler(handler_input)


@sb.request_handler(can_handle_func=is_intent_name('AbfrageEigeneAdresseIntent'))
def abfrage_eigene_adresse_handler_wrapper(handler_input) -> Response:
    return abfrage_eigene_adresse_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('InseratErzeugenIntent')
    and handler_input.request_envelope.request.dialog_state == DialogState.STARTED
)
def inserat_erzeugen_start_handler_wrapper(handler_input) -> Response:
    return inserat_erzeugen_start_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('InseratErzeugenIntent')
    and handler_input.request_envelope.request.dialog_state == DialogState.IN_PROGRESS
)
def inserat_erzeugen_in_progress_handler_wrapper(handler_input) -> Response:
    return inserat_erzeugen_in_progress_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('InseratErzeugenIntent')
    and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED
)
def inserat_erzeugen_completed_handler_wrapper(handler_input) -> Response:
    return inserat_erzeugen_completed_handler(handler_input)


@sb.request_handler(can_handle_func=is_intent_name('BenutzerLinkingIntent'))
def benutzer_linking_handler_wrapper(handler_input) -> Response:
    return benutzer_linking_handler(handler_input)


"""
Eigene Interceptoren, um Vor- & Nachbedingungen zu schaffen
- localization_request_interceptor
"""


@sb.global_request_interceptor()
def localization_request_interceptor(handler_input):
    logger.info('Localization Interceptor wird ausgeführt...')

    try:
        with open('languages/de-DE.json') as sprach_prompt_daten:
            sprach_prompts = json.load(sprach_prompt_daten)
            handler_input.attributes_manager.request_attributes['_'] = sprach_prompts
    except FileNotFoundError as e:
        logger.warning(f'Alexa-Sprachbefehle konnten nicht geladen werden: {e}')
        exit()


skill_adapter = SkillAdapter(skill=sb.create(), skill_id=1, app=app)


@app.route('/', methods=['GET', 'POST'])
def invoke_skill():
    return skill_adapter.dispatch_request()


if __name__ == '__main__':
    app.run()
