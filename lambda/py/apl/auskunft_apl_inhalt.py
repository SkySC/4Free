def get_apl_daten():
    # Beispielfragen zu den einzelnen Intents
    intent_fragen = [
        "Anzeige schalten: \"Neue Anzeige\"",
        "Suchfunktion: \"Suche starten\"",
        "Eigene Artikel: \"Zeige meine Artikel\"",
        "Suchergebnisse wiederholen: \"Suchergebnisse anzeigen\"",
        "Suchradius einschränken: \"Suchradius ändern\"",
        "Adressdaten abfragen: \"Wie lautete meine Adresse?\"",
        "Benutzerkonto: \"Benutzerkonto verbinden\"",
        "Entwicklerinformationen: \"Wer hat 4Free entwickelt?\""
    ]

    listen_eintraege = []
    for eintrag in intent_fragen:
        listen_eintraege.append({
            "primaryText": eintrag,
            "primaryAction": [
                {
                    "type": "SetValue",
                    "componentId": "aktionsListe",
                    "property": "headerTitle",
                    "value": f"{eintrag} ausgewählt"
                }
            ]
        })

    auskunft_daten = {
        "textListData": {
            "type": "object",
            "objectId": "textListSample",
            "backgroundImage": {
                "contentDescription": None,
                "smallSourceUrl": None,
                "largeSourceUrl": None,
                "sources": [
                    {
                        "url": "https://cdn.pixabay.com/photo/2016/05/28/00/06/gift-1420830_960_720.jpg",
                        "size": "large"
                    }
                ]
            },
            "title": "Meine Funktionen",
            "listItems": listen_eintraege
        }
    }

    return auskunft_daten
