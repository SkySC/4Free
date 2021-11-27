import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard
from flask import Flask
from flask_ask_sdk.skill_adapter import SkillAdapter

import Database
import EntwicklerInfoIntent
import EigeneInserateIntent
import RadiusEinstellenIntent
import AccountLinking

# logging.basicConfig(fiilename='logfile.log', level=logging.ERROR)

app = Flask(__name__)

sb = SkillBuilder()

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
    speech_text = 'Willkommen bei For Free!'
    return AccountLinking.benutzer_authorisieren(handler_input)

"""
    return (
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard(speech_text)
        ).set_should_end_session(False).response
    )
"""


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input) -> Response:
    """Handler for Help Intent."""
    speech_text = "Um dir zu helfen, kann ich dir einige Kommandos nennen, welche ich derzeit verstehe. \
                    Sage zum Beispiel: Was sind die wichtigsten Kommandos?"
    ask_text = "Was möchtest du von mir wissen?"

    return handler_input.response_builder.speak(speech_text).ask(ask_text).response


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name("AMAZON.CancelIntent")(handler_input) or
    is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input) -> Response:
    """Single handler for Cancel and Stop Intent."""
    speech_text = "Auf Wiedersehen, bis zum nächsten Mal!"

    return (
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Auf Wiedersehen!")).response
    )


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input) -> Response:
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    speech_text = "Leider kann ich dir damit nicht weiterhelfen"
    reprompt_text = "Du kannst mich zum Beispiel darum bitten nach Inseraten zu suchen oder welche zu erstellen. \
                    Sage dafür beispielsweise: Artikel suchen oder Inserat erzeugen!"

    return handler_input.response_builder.speak(speech_text).ask(reprompt_text).response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input) -> Response:
    """Handler for Session End."""
    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception) -> Response:
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    logging.error(exception, exc_info=True)

    speech_text = "Tut mir Leid, es gab leider ein unerwartetes Problem. Versuche es bitte erneut!"

    return handler_input.response_builder.speak(speech_text).response


"""
Custom Intent Handler in Decorator-Style
- EntwicklerInfoIntent
"""


@sb.request_handler(can_handle_func=is_intent_name('EntwicklerInfoIntent'))
def entwickler_info_handler(handler_input) -> Response:
    return EntwicklerInfoIntent.entwickler_info_handler(handler_input)


@sb.request_handler(can_handle_func=is_intent_name('EigeneInserateIntent'))
def eigene_inserate_handler(handler_input) -> Response:
    return EigeneInserateIntent.eigene_inserate_handler(handler_input)


@sb.request_handler(can_handle_func=is_intent_name('RadiusEinstellenIntent'))
def radius_einstellen_handler(handler_input) -> Response:
    return RadiusEinstellenIntent.radius_einstellen_handler(handler_input)


skill_adapter = SkillAdapter(skill=sb.create(), skill_id=1, app=app)


@app.route('/', methods=['GET', 'POST'])
def invoke_skill():
    return skill_adapter.dispatch_request()


if __name__ == '__main__':
    app.run()
