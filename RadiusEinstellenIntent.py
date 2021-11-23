import Database


def radius_einstellen_handler(handler_input):
    """Suchradius einstellen"""
    tmp_uid = 'u1234'
    umkreis_slot_value = handler_input.request_envelope.request.intent.slots['radius'].value

    speech_text = f'Dein Suchradius wurde erfolgreich auf {umkreis_slot_value} Kilometer geändert.'
    speech_reprompt = 'Auf wie viel Kilometer möchtest du den Suchradius stellen?'

    db = Database.MongoDB
    if db.benutzer_get_umkreis(tmp_uid) == umkreis_slot_value:
        speech_text = f'Dein aktueller Suchradius beträgt bereits {umkreis_slot_value} Kilometer.'
    else:
        db.benutzer_set_umkreis(tmp_uid, umkreis_slot_value)
    # Falls Wert nicht gesetzt werden konnte
    if db.benutzer_hat_einstellungen_eintrag(tmp_uid) is False:
        speech_text = 'Tut mir Leid, beim ändern des Suchradius ist ein Fehler aufgetreten. Bitte versuche es erneut.'

    return (
        handler_input.response_builder
            .speak(speech_text)
            .ask(speech_reprompt)
            .set_should_end_session(False).response
    )
