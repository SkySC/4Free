import logging
import random
import sys

from ask_sdk_model.dialog import ElicitSlotDirective, DelegateDirective

import Benutzer
import Database

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
        return response_builder.speak(
            sprach_prompts['SUCHE_NICHT_GESTARTET_ODER_KEINE_TREFFER_FEHLER']
        ).response

    return response_builder.speak(
        sprach_prompts['VORHERIGE_SUCHERGEBNISSE_WEITERLEITUNG']
    ).add_directive(
        DelegateDirective(updated_intent=handler_input.request_envelope.request.intent)
    ).response


def suchergebnisse_in_progress_handler(handler_input):
    """
    Suchergebnisse vorlesen mit Möglichkeit zur Navigation, Kontaktieren des Anbieters und das Setzen vor Favoriten
    """
    response_builder = handler_input.response_builder
    attributes_manager = handler_input.attributes_manager
    sprach_prompts = attributes_manager.request_attributes['_']
    session_attr = attributes_manager.session_attributes
    intent = handler_input.request_envelope.request.intent
    # Flag um zu vermeiden, dass das Ergebnis für Cases außer 'None, Vorherige, Nächste' ausgegeben wird
    artikel_ausgeben = False
    sprach_ausgabe = '<speak>'
    match intent.slots['aktion'].value:
        # Slot zu Beginn leer <=> Erste Ausgabe
        case None:
            artikel_ausgeben = True
            if len(session_attr['suchergebnisse']) == 1:
                sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_EINEN_TREFFER']
            else:
                sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_MEHRERE_TREFFER'].format(
                    len(session_attr['suchergebnisse'])
                )
        # Zurück zum Start
        case 'zurück' | 'umkehren' | 'zurückkehren' | 'beenden' | 'suche verlassen':
            return response_builder.add_directive(
                DelegateDirective(updated_intent=intent)
            ).response
        # Nächsten Treffer
        case 'nächste' | 'nächster' | 'weiter' | 'nächstes ergebnis' | 'nächstes resultat' | 'nächster artikel' | \
             'nächsten artikel' | 'nächsten artikel zeigen' | 'nächstes resultat zeigen':
            # Zeiger++
            if session_attr['ergebnis_zeiger'] < len(session_attr['suchergebnisse']) - 1:
                artikel_ausgeben = True
                session_attr['ergebnis_zeiger'] += 1
            else:
                sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_BEREITS_LETZTER_ARTIKEL']
        # Vorherigen Treffer
        case 'vorherige' | 'vorheriger' | 'zurück' | 'vorheriges ergebnis' | 'vorheriges resultat' | \
             'vorheriger artikel' | 'vorherigen artikel' | 'vorheriges ergebnis zeigen' | 'vorherigen artikel zeigen':
            # Zeiger--
            if session_attr['ergebnis_zeiger'] > 0:
                artikel_ausgeben = True
                session_attr['ergebnis_zeiger'] -= 1
            else:
                sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_BEREITS_ERSTER_ARTIKEL']
        # Zum letzten Artikel springen
        case 'springe zum letzten artikel' | 'letzter artikel' | 'navigiere zum letzten artikel' | \
             'zeige mir den letzten artikel':

            if session_attr['ergebnis_zeiger'] >= len(session_attr['suchergebnisse']) - 1:
                sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_BEREITS_LETZTER_ARTIKEL']
            else:
                artikel_ausgeben = True
                session_attr['ergebnis_zeiger'] = len(session_attr['suchergebnisse']) - 1
                sprach_ausgabe += sprach_prompts['LETZTER_ARTIKEL_ANKUENDIGUNG']
        # Zum ersten Artikel springen
        case 'springe zum ersten artikel' | 'erster artikel' | 'navigiere zum ersten artikel' | \
             'zeige mir den ersten artikel':

            if session_attr['ergebnis_zeiger'] <= 0:
                sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_BEREITS_ERSTER_ARTIKEL']
            else:
                artikel_ausgeben = True
                session_attr['ergebnis_zeiger'] = 0
                sprach_ausgabe += sprach_prompts['ERSTER_ARTIKEL_ANKUENDIGUNG']
        # Artikel merken
        case 'favorisieren' | 'markieren' | 'merken' | 'merke dir das' | 'merke dir den artikel' | \
             'markiere den artikel' | 'markiere das' | 'favorisiere den artikel' | 'favorisiere das' | \
             'setze einen favorit' | 'setze eine marktierung' | 'markierung setzen' | 'favorit setzen' | \
             'artikel merken' | 'inserat merken' | 'ich mag den artikel' | 'like den artikel' | 'artikel liken':
            # Prüfen, ob Benutzerkonto besteht
            if Benutzer.AmazonBenutzer.benutzer_existiert():
                # Artikel-Id in DB unter Benutzereinstellungen speichern
                artikel_id = session_attr['suchergebnisse'][session_attr['ergebnis_zeiger']]['_id']
                if Database.MongoDB.favorit_setzen(artikel_id):
                    sprach_ausgabe += random.choice(sprach_prompts['ARTIKEL_FAVORISIEREN_ERFOLG'])
                else:
                    sprach_ausgabe += sprach_prompts['ARTIKEL_BEREITS_FAVORISIERT_ODER_FEHLER']

            else:
                sprach_ausgabe += sprach_prompts['FAVORIT_BENOETIGT_BENUTZER_FEHLER']
        # Favorit entfernen
        case 'favorit entfernen' | 'markierung entfernen' | 'entfernen':
            if Benutzer.AmazonBenutzer.benutzer_existiert():
                # Artikel aus DB entfernen
                artikel_id = session_attr['suchergebnisse'][session_attr['ergebnis_zeiger']]['_id']
                if Database.MongoDB.favorit_entfernen(artikel_id):
                    sprach_ausgabe += random.choice(sprach_prompts['ARTIKEL_FAVORIT_ENTFERNEN_ERFOLG'])
                else:
                    sprach_ausgabe += sprach_prompts['ARTIKEL_FAVORIT_ENTFERNEN_FEHLER']
        # Detaillierte Ausgabe
        case 'details' | 'zeige mir details' | 'zeige mir die details' | 'zeige mir bitte die details' | \
             'mehr details' | 'kannst du mir mehr darüber erzählen' | 'erzähle mir bitte mehr darüber' | \
             'erzähle mir mehr darüber' | 'was weißt du noch über diesen artikel' | 'erzähle mir mehr' | \
             'erzähle mir mehr über den artikel' | 'ich möchte mehr wissen' | 'ich möchte mehr darüber wissen' | \
             'der artikel interessiert mich' | 'ich möchte mehr darüber erfahren' | 'sage mir dazu mehr' | \
             'nenne mir weitere details' | 'nenne weitere details' | 'weitere details':

            aktueller_artikel = session_attr['suchergebnisse'][session_attr['ergebnis_zeiger']]
            # Bestimmte Satzbausteine anpassen, so dass es natürlicher klingt
            aktueller_artikel_abholung_satzbaustein = 'eine' \
                if aktueller_artikel['artikeldaten']['abholung'] == 'ja' \
                else 'keine'
            sprach_ausgabe += sprach_prompts['SUCHERGEBNIS_DETAILS'].format(
                aktueller_artikel['artikeldaten']['material'],
                aktueller_artikel['artikeldaten']['laenge'],
                aktueller_artikel['artikeldaten']['breite'],
                aktueller_artikel['artikeldaten']['hoehe'],
                aktueller_artikel['meta_beschreibung']['anbieter_name'],
                aktueller_artikel_abholung_satzbaustein,
                aktueller_artikel['artikeldaten']['anmerkung']
            )
        # Anbieter kontaktieren
        case 'kontaktieren' | 'kontaktiere den anbieter' | 'nachricht hinterlassen' | 'nachricht an den anbieter' | \
             'nachricht hinterlassen' | 'anbieter kontaktieren' | 'nachricht an den anbieter hinterlassen':

            logging.info('Anbieter kontaktieren')

            sprach_ausgabe += sprach_prompts['FEATURE_NICHT_IMPLEMENTIERT']
        # Ungültige Aktion -> Reprompt
        case _:
            sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_AKTION_PROMPT']
    # Suchergebnis zusammenbauen, falls Flag gesetzt
    if artikel_ausgeben:
        aktueller_artikel = session_attr['suchergebnisse'][session_attr['ergebnis_zeiger']]
        # Bestimmte Satzbausteine anpassen, so dass es natürlicher klingt
        aktueller_artikel_stueckzahl_satzbaustein = 'ein' \
            if aktueller_artikel['artikeldaten']['stueckzahl'] == 1 \
            else aktueller_artikel['artikeldaten']['stueckzahl']
        aktueller_artikel_zustand_satzbaustein = aktueller_artikel['artikeldaten']['zustand'] + 'en' \
            if aktueller_artikel['artikeldaten']['zustand'] not in ['ohne schäden', 'klasse', 'ohne mängel'] \
            else aktueller_artikel['artikeldaten']['zustand']

        sprach_ausgabe += sprach_prompts['SUCHERGEBNIS_ZUSAMMENFASSUNG'].format(
            aktueller_artikel['meta_beschreibung']['anbieter_name'],
            aktueller_artikel['meta_beschreibung']['erstellungs_datum'].split(' ')[0],
            aktueller_artikel['meta_beschreibung']['anbieter_name'],
            aktueller_artikel_stueckzahl_satzbaustein,
            aktueller_artikel['artikeldaten']['bezeichnung'],
            aktueller_artikel['artikeldaten']['farbe'],
            aktueller_artikel['artikeldaten']['hersteller'],
            aktueller_artikel_zustand_satzbaustein
        )
    sprach_ausgabe += '</speak>'

    logging.info(f'{sprach_ausgabe=}')

    return response_builder.speak(sprach_ausgabe).ask(
        random.choice(sprach_prompts['AKTION_REPROMPT'])
    ).add_directive(
        ElicitSlotDirective(slot_to_elicit='aktion')
    ).response


def suchergebnisse_completed_handler(handler_input):
    attributes_manager = handler_input.attributes_manager
    sprach_prompts = attributes_manager.request_attributes['_']
    # Ergebnis-Zeiger für wiederholte Ergebnis-Ausgabe zurücksetzen
    attributes_manager.session_attributes['ergebnis_zeiger'] = 0

    return handler_input.response_builder.speak(
        sprach_prompts['SUCHERGEBNISSE_VERLASSEN']
    ).response
