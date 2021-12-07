import logging

import Database

from ask_sdk_core.utils import get_account_linking_access_token


def radius_einstellen_handler(handler_input):
    """Suchradius einstellen"""
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    response_builder.set_should_end_session(False)
    # response_builder.ask(sprach_prompts['SUCHRADIUS_REPROMPT'])

    db = Database.MongoDB
    umkreis_slot_wert = int(handler_input.request_envelope.request.intent.slots['radius'].value)
    if get_account_linking_access_token(handler_input):
        if db.benutzer_get_umkreis() == umkreis_slot_wert:
            response_builder.speak(str(sprach_prompts['SUCHRADIUS_IDENTISCH_FEHLER']).format(umkreis_slot_wert))
        else:
            db.benutzer_set_umkreis(umkreis_slot_wert)
            response_builder.speak(str(sprach_prompts['SUCHRADIUS_SPEICHERN_ERFOLG']).format(umkreis_slot_wert))
        # Falls Wert nicht gesetzt werden konnte
        if db.benutzer_hat_einstellungen_eintrag() is False:
            response_builder.speak(sprach_prompts['SUCHRADIUS_SPEICHERN_FEHLER'])
    # Store radius in session attribute, if no account is linked
    else:
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr['suchradius'] = umkreis_slot_wert
        logging.info(f'{session_attr["suchradius"]=}')

        response_builder.speak(str(sprach_prompts['SUCHRADIUS_SPEICHERN_ERFOLG']).format(session_attr['suchradius']))

    return response_builder.response
