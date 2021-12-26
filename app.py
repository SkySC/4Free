import json
import logging
import random
import sys

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response, DialogState
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
from AbfrageEigeneAdresseIntent import abfrage_eigene_adresse_handler, get_geraete_standortdaten
from InseratErzeugenIntent import (
    inserat_erzeugen_start_handler, inserat_erzeugen_in_progress_handler, inserat_erzeugen_completed_handler
)
from BenutzerLinkingIntent import benutzer_linking_handler
from AccountLinking import benutzer_authorisieren
from SucheStartenIntent import suche_starten_handler
from EinfacheSucheIntent import (
    einfache_suche_start_handler, einfache_suche_in_progress_handler, einfache_suche_completed_handler
)
from DetaillierteSucheIntent import (
    detaillierte_suche_start_handler, detaillierte_suche_in_progress_handler, detaillierte_suche_completed_handler
)
from SuchergebnisseIntent import (
    suchergebnisse_start_handler, suchergebnisse_in_progress_handler, suchergebnisse_completed_handler
)

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
    """
    Handler für den Skillstart
    """
    attributes_manager = handler_input.attributes_manager
    # Sprachdaten laden
    sprach_prompts = attributes_manager.request_attributes['_']
    # Session-Attribute laden
    session_attr = attributes_manager.session_attributes
    session_attr['plz'] = get_geraete_standortdaten(handler_input)[1]
    session_attr['land'] = 'DE' if get_geraete_standortdaten(handler_input)[3] == 'Deutschland' \
        else get_geraete_standortdaten(handler_input)[3]
    logging.info(f'{session_attr["plz"]=} | {session_attr["land"]=}')

    # Account-Linking starten, falls noch kein Benutzerkonto, sonst überspringen
    benutzer_linked, response_builder = benutzer_authorisieren(handler_input)
    response_builder.set_should_end_session(False)
    # speech_output = sprach_prompts['START']
    # Anhand von Geräte-ID prüfen, ob Benutzer den Skill das erste Mal startet
    geraete_id = handler_input.request_envelope.context.system.device.device_id
    if db.skill_erststart(geraete_id):
        # Onboarding einleiten
        logging.info('Onboarding wird gestartet...')

        if db.registriere_benutzer_geraet(geraete_id):
            logging.info('Gerät wurde erfolgreich registriert')

        else:
            logging.warning('Fehler bei der Registrierung des Geräts')

        # Beim Erststart dem Benutzer erklären, wie er das Account-Linking durchführt
        if not benutzer_linked:
            response_builder.speak(sprach_prompts['BENUTZER_ONBOARDING_LINKING_ANWEISUNGEN'])

    else:
        logging.info(f'{db.skill_erststart(geraete_id)=}')

        if benutzer_linked:
            benutzer_name = Benutzer.AmazonBenutzer.get_benutzer_namen()
            response_builder.speak(random.choice(sprach_prompts['BENUTZER_LINKED_BEGRUESSUNG']).format(benutzer_name))
        else:
            response_builder.speak(random.choice(sprach_prompts['BENUTZER_BEGRUESSUNG']))

    # Suchradius in Session-Attribut speichern <=> Kein Benutzerkonto
    if not benutzer_linked:
        # Standard-Suchradius von 15km
        session_attr['suchradius'] = 15
        logging.info(f'{session_attr=}')

    return response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input) -> Response:
    """
    Handler für die Hilfeseite
    """
    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']

    response_builder = handler_input.response_builder
    response_builder.speak(sprach_prompts['HILFESEITE_EINLEITUNG']).ask(sprach_prompts['HILFESEITE_FRAGE_PROMPT'])

    return response_builder.response


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name("AMAZON.CancelIntent")(handler_input) or
    is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input) -> Response:
    """
    Handler, um den Skill zu beenden
    """
    # Sprachdaten laden
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder

    benutzer_name = Benutzer.AmazonBenutzer.get_benutzer_namen()
    sprach_ausgabe = random.choice(sprach_prompts['BENUTZER_VERABSCHIEDEN'])\
        .format(f'{"" if benutzer_name is None else benutzer_name}')
    response_builder.speak(sprach_ausgabe)
    response_builder.set_card(SimpleCard(sprach_ausgabe))

    return response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input) -> Response:
    """
    Handler, welcher ausgeführt wird, wenn kein passender Intent gefunden wird (nur in 'en-US')
    """
    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    response_builder.set_should_end_session(False)

    response_builder.speak(sprach_prompts['FALLBACK'])

    return response_builder.response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input) -> Response:
    """
    Handler, um die Sitzung zu beenden -> Weiterleitung an cancel_and_stop_intent_handler
    """
    # Call cancel_and_stop_intent instead
    return cancel_and_stop_intent_handler(handler_input)


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception) -> Response:
    """
    Handler, um alle allgemeinen Exceptions abzufangen und auszugeben
    """
    # Load language data
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder

    logging.exception(exception, exc_info=True)
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
    is_intent_name('InseratErzeugenIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.STARTED
)
def inserat_erzeugen_start_handler_wrapper(handler_input) -> Response:
    return inserat_erzeugen_start_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('InseratErzeugenIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.IN_PROGRESS
)
def inserat_erzeugen_in_progress_handler_wrapper(handler_input) -> Response:
    return inserat_erzeugen_in_progress_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('InseratErzeugenIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED
)
def inserat_erzeugen_completed_handler_wrapper(handler_input) -> Response:
    return inserat_erzeugen_completed_handler(handler_input)


@sb.request_handler(can_handle_func=is_intent_name('BenutzerLinkingIntent'))
def benutzer_linking_handler_wrapper(handler_input) -> Response:
    return benutzer_linking_handler(handler_input)


@sb.request_handler(can_handle_func=is_intent_name('SucheStartenIntent'))
def suche_starten_handler_wrapper(handler_input) -> Response:
    return suche_starten_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('EinfacheSucheIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.STARTED
)
def einfache_suche_start_handler_wrapper(handler_input) -> Response:
    return einfache_suche_start_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('EinfacheSucheIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.IN_PROGRESS
)
def einfache_suche_in_progress_handler_wrapper(handler_input) -> Response:
    return einfache_suche_in_progress_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('EinfacheSucheIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED
)
def einfache_suche_completed_handler_wrapper(handler_input) -> Response:
    return einfache_suche_completed_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('DetaillierteSucheIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.STARTED
)
def detaillierte_suche_start_handler_wrapper(handler_input) -> Response:
    return detaillierte_suche_start_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('DetaillierteSucheIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.IN_PROGRESS
)
def detaillierte_suche_in_progress_handler_wrapper(handler_input) -> Response:
    return detaillierte_suche_in_progress_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('DetaillierteSucheIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED
)
def detaillierte_suche_completed_handler_wrapper(handler_input) -> Response:
    return detaillierte_suche_completed_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('SuchergebnisseIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.STARTED
)
def suchergebnisse_start_handler_wrapper(handler_input) -> Response:
    return suchergebnisse_start_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('SuchergebnisseIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.IN_PROGRESS
)
def suchergebnisse_in_progress_handler_wrapper(handler_input) -> Response:
    return suchergebnisse_in_progress_handler(handler_input)


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name('SuchergebnisseIntent')(handler_input)
    and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED
)
def suchergebnisse_completed_handler_wrapper(handler_input) -> Response:
    return suchergebnisse_completed_handler(handler_input)


"""
Eigene Interceptoren, um Vor- & Nachbedingungen zu schaffen
- localization_request_interceptor
- logging_request_interceptor
"""


@sb.global_request_interceptor()
def localization_request_interceptor(handler_input):
    logger.info('Localization Interceptor wird ausgeführt...')

    try:
        with open('languages/de-DE.json') as sprach_prompt_daten:
            sprach_prompts = json.load(sprach_prompt_daten)
            handler_input.attributes_manager.request_attributes['_'] = sprach_prompts
    except FileNotFoundError as e:
        logger.exception(f'Alexa-Sprachbefehle konnten nicht geladen werden: {e}')
        exit()


@sb.global_request_interceptor()
def logging_request_interceptor(handler_input):
    logging.info(f'{handler_input.request_envelope.request.object_type=}')


skill_adapter = SkillAdapter(skill=sb.create(), skill_id=1, app=app)


@app.route('/', methods=['GET', 'POST'])
def invoke_skill():
    return skill_adapter.dispatch_request()


if __name__ == '__main__':
    app.run()
