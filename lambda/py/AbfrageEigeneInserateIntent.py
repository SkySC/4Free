import logging
import sys

from ask_sdk_model.dialog import ElicitSlotDirective, DelegateDirective

import Benutzer
import Database

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('__name__')


def abfrage_eigene_inserate_start_handler(handler_input):
    # Sprachdaten laden
    attributes_manager = handler_input.attributes_manager
    sprach_prompts = attributes_manager.request_attributes['_']
    session_attr = attributes_manager.session_attributes
    response_builder = handler_input.response_builder

    if not Benutzer.AmazonBenutzer.benutzer_existiert():
        return response_builder.speak(
            sprach_prompts['EIGENE_INSERATE_ABFRAGEN_BENUTZER_NICHT_LINKED']
        ).set_should_end_session(
            False
        ).response

    anzahl_eigene_inserate = Database.MongoDB.zaehle_eigene_inserate()
    session_attr['ergebnis_zeiger'] = 0

    match anzahl_eigene_inserate:
        case 0:
            return response_builder.speak(
                sprach_prompts['KEINE_AKTIVEN_EIGENEN_INSERATE']
            ).response
        case 1:
            response_builder.speak(sprach_prompts['ANZAHL_AKTIVE_EIGENE_INSERATE_EINS'])
        case None:
            response_builder.speak(sprach_prompts['ALLGEMEINER_FEHLER'])
        case _:
            response_builder.speak(sprach_prompts['ANZAHL_AKTIVE_EIGENE_INSERATE'].format(
                anzahl_eigene_inserate
            ))

    return response_builder.add_directive(
        DelegateDirective(updated_intent=handler_input.request_envelope.request.intent)
    ).response


def abfrage_eigene_inserate_in_progress_handler(handler_input):
    """Eigene Inserate ausgeben"""
    # Sprachdaten laden
    attributes_manager = handler_input.attributes_manager
    sprach_prompts = attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    session_attr = attributes_manager.session_attributes
    intent = handler_input.request_envelope.request.intent
    slots = intent.slots

    artikel_ausgeben = True
    sprach_ausgabe = '<speak>'
    match slots['aktion'].value:
        # Slots zu Beginn leer <=> Als erstes ausgeführt, um eigene Inserate zu laden
        case None:
            session_attr['eigene_inserate'] = Database.MongoDB.get_eigene_inserate(
                slots['reihenfolge'].value
            )
            logging.info(f'{session_attr["eigene_inserate"]=}')
            # Ungültige Sortierung angegeben
            if not session_attr['eigene_inserate']:
                # Alexa Slot Validation verwenden <=> Sitzung endet nach 2 falschen Angaben
                return response_builder.add_directive(
                    DelegateDirective(updated_intent=intent)
                ).response
        # Zurück zum Start
        case 'zurück' | 'umkehren' | 'zurückkehren':
            return response_builder.add_directive(
                DelegateDirective(updated_intent=intent)
            ).response
        # Nächsten Treffer
        case 'nächste' | 'nächster' | 'weiter' | 'nächstes ergebnis' | 'nächstes resultat' | 'nächster artikel' | \
             'nächsten artikel' | 'nächsten artikel zeigen' | 'nächstes resultat zeigen':
            # Zeiger++
            if session_attr['ergebnis_zeiger'] < len(session_attr['eigene_inserate']) - 1:
                session_attr['ergebnis_zeiger'] += 1
            else:
                artikel_ausgeben = False
                sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_BEREITS_LETZTER_ARTIKEL']
        # Vorherigen Treffer
        case 'vorherige' | 'vorheriger' | 'zurück' | 'vorheriges ergebnis' | 'vorheriges resultat' | \
             'vorheriger artikel' | 'vorherigen artikel' | 'vorheriges ergebnis zeigen' | 'vorherigen artikel zeigen':
            # Zeiger--
            if session_attr['ergebnis_zeiger'] > 0:
                session_attr['ergebnis_zeiger'] -= 1
            else:
                artikel_ausgeben = False
                sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_BEREITS_ERSTER_ARTIKEL']
        # Zum letzten Artikel springen
        case 'springe zum letzten artikel' | 'letzter artikel' | 'navigiere zum letzten artikel' | \
             'zeige mir den letzten artikel':

            if session_attr['ergebnis_zeiger'] >= len(session_attr['eigene_inserate']) - 1:
                artikel_ausgeben = False
                sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_BEREITS_LETZTER_ARTIKEL']
            else:
                session_attr['ergebnis_zeiger'] = len(session_attr['eigene_inserate']) - 1
                sprach_ausgabe += sprach_prompts['LETZTER_ARTIKEL_ANKUENDIGUNG']

        # Zum ersten Artikel springen
        case 'springe zum ersten artikel' | 'erster artikel' | 'navigiere zum ersten artikel' | \
             'zeige mir den ersten artikel':

            if session_attr['ergebnis_zeiger'] <= 0:
                artikel_ausgeben = False
                sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_BEREITS_ERSTER_ARTIKEL']
            else:
                session_attr['ergebnis_zeiger'] = 0
                sprach_ausgabe += sprach_prompts['ERSTER_ARTIKEL_ANKUENDIGUNG']

        # Detaillierte Ausgabe
        case 'details' | 'zeige mir details' | 'zeige mir die details' | 'zeige mir bitte die details' | \
             'mehr details' | 'kannst du mir mehr darüber erzählen' | 'erzähle mir bitte mehr darüber' | \
             'erzähle mir mehr darüber' | 'was weißt du noch über diesen artikel' | 'erzähle mir mehr' | \
             'erzähle mir mehr über den artikel' | 'ich möchte mehr wissen' | 'ich möchte mehr darüber wissen' | \
             'der artikel interessiert mich' | 'ich möchte mehr darüber erfahren' | 'sage mir dazu mehr' | \
             'nenne mir weitere details' | 'nenne weitere details' | 'weitere details':
            artikel_ausgeben = False
            aktueller_artikel = session_attr['eigene_inserate'][session_attr['ergebnis_zeiger']]
            # Bestimmte Satzbausteine anpassen, so dass es natürlicher klingt
            aktueller_artikel_abholung_satzbaustein = '' if aktueller_artikel['artikeldaten']['abholung'] == 'ja' \
                else 'nicht'
            sprach_ausgabe += sprach_prompts['EIGENE_INSERATE_DETAILS'].format(
                aktueller_artikel['artikeldaten']['material'],
                aktueller_artikel['artikeldaten']['laenge'],
                aktueller_artikel['artikeldaten']['breite'],
                aktueller_artikel['artikeldaten']['hoehe'],
                aktueller_artikel_abholung_satzbaustein,
                aktueller_artikel['artikeldaten']['anmerkung']
            )
        # Inserat entfernen
        case 'inserat löschen' | 'inserat entfernen' | 'artikel löschen' | 'artikel entfernen' | \
             'lösche meinen artikel' | 'entferne meinen artikel' | 'lösche diesen artikel' | \
             'entferne diesen artikel' | 'entferne den artikel' | 'entferne dieses inserat':

            artikel_ausgeben = False
            artikel_id = session_attr['eigene_inserate'][session_attr['ergebnis_zeiger']]['_id']
            if Database.MongoDB.entferne_eigenes_inserat(artikel_id):
                # Eigene Inserate mit Sortierung aktualisieren
                session_attr['eigene_inserate'] = Database.MongoDB.get_eigene_inserate(
                    slots['reihenfolge'].value
                )
                logging.info(f'{session_attr["eigene_inserate"]=}')
                # Zeiger aktualisieren, falls == len(eigene_inserate) - 1
                session_attr['ergebnis_zeiger'] -= 1 \
                    if len(session_attr['eigene_inserate']) >= session_attr['ergebnis_zeiger'] \
                    else 0
                sprach_ausgabe += sprach_prompts['INSERAT_ERFOLGREICH_GELOESCHT']
            else:
                sprach_ausgabe += sprach_prompts['INSERAT_LOESCHEN_FEHLER']
            # Prüfen, ob Benutzer noch Inserat hat, sonst rausnavigieren
            if Database.MongoDB.zaehle_eigene_inserate() == 0:
                return response_builder.speak(
                    sprach_prompts['KEINE_AKTIVEN_EIGENEN_INSERATE']
                ).add_directive(
                    DelegateDirective(updated_intent=intent)
                )

        # Ungültige Aktion -> Reprompt
        case _:
            artikel_ausgeben = False
            sprach_ausgabe += sprach_prompts['SUCHERGEBNISSE_AKTION_PROMPT']
    # Suchergebnis zusammenbauen, falls Flag gesetzt
    if artikel_ausgeben:
        aktueller_artikel = session_attr['eigene_inserate'][session_attr['ergebnis_zeiger']]
        # Bestimmte Satzbausteine anpassen, so dass es natürlicher klingt
        aktueller_artikel_stueckzahl_satzbaustein = 'ein' if aktueller_artikel['artikeldaten']['stueckzahl'] == 1 \
            else aktueller_artikel['artikeldaten']['stueckzahl']
        aktueller_artikel_zustand_satzbaustein = aktueller_artikel['artikeldaten']['zustand'] + 'en' \
            if aktueller_artikel['artikeldaten']['zustand'] not in ['ohne schäden', 'klasse', 'ohne mängel'] \
            else aktueller_artikel['artikeldaten']['zustand']

        sprach_ausgabe += sprach_prompts['EIGENE_INSERATE_ZUSAMMENFASSUNG'].format(
            session_attr['ergebnis_zeiger'] + 1,
            aktueller_artikel['meta_beschreibung']['erstellungs_datum'].split(' ')[0],
            aktueller_artikel_stueckzahl_satzbaustein,
            aktueller_artikel['artikeldaten']['bezeichnung'],
            aktueller_artikel['artikeldaten']['farbe'],
            aktueller_artikel['artikeldaten']['hersteller'],
            aktueller_artikel_zustand_satzbaustein
        )
    sprach_ausgabe += '</speak>'

    return response_builder.speak(sprach_ausgabe).ask(
        sprach_prompts['AKTION_REPROMPT']
    ).add_directive(
        ElicitSlotDirective(slot_to_elicit='aktion')
    ).response


def abfrage_eigene_inserate_completed_handler(handler_input):
    # Sprachdaten laden
    attributes_manager = handler_input.attributes_manager
    sprach_prompts = attributes_manager.request_attributes['_']
    response_builder = handler_input.response_builder
    # Session Attribute für das Zwischenspeichern der Inserate löschen
    attributes_manager.session_attributes.pop('eigene_inserate', None)
    attributes_manager.session_attributes.pop('ergebnis_zeiger', None)

    return response_builder.speak(
        sprach_prompts['ZURUECK_ZUM_START']
    ).response
