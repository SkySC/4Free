import logging

import Benutzer
import Database


def radius_einstellen_handler(handler_input):
    """Suchradius verändern"""
    sprach_prompts = handler_input.attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder

    response_builder.set_should_end_session(False)

    db = Database.MongoDB
    umkreis_slot_wert = int(handler_input.request_envelope.request.intent.slots['radius'].value)
    if Benutzer.AmazonBenutzer.benutzer_existiert():
        if db.benutzer_get_umkreis() == umkreis_slot_wert:
            response_builder.speak(str(sprach_prompts['SUCHRADIUS_IDENTISCH_FEHLER'])
                                   .format(umkreis_slot_wert))
        else:
            db.benutzer_set_umkreis(umkreis_slot_wert)
            response_builder.speak(str(sprach_prompts['SUCHRADIUS_SPEICHERN_ERFOLG'])
                                   .format(umkreis_slot_wert))
        # Prüfen, ob Wert in DB gespeichert wurde
        if db.benutzer_hat_einstellungen_eintrag() is False:
            response_builder.speak(sprach_prompts['SUCHRADIUS_SPEICHERN_FEHLER'])
    # Falls kein Benutzerkonto verlinkt -> Radius in Session Attribut speichern
    else:
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr['suchradius'] = umkreis_slot_wert
        logging.info(f'{session_attr["suchradius"]=}')

        response_builder.speak(str(sprach_prompts['SUCHRADIUS_SPEICHERN_ERFOLG'])
                               .format(session_attr['suchradius']))

    return response_builder.response
