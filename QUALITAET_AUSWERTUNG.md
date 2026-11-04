# Prüfung von Öffnung und Schärfebereich

Die lokale Auswertung enthält zwei zusätzliche Schritte:

1. Nach Markierung des Hauptmotivs **Schärfebereich prüfen & Vorschläge suchen** wählen. Vorschläge entstehen aus sieben über die Folge verteilten Bildern oder einer gespeicherten vollständigen Auswertung derselben ZIP. Die Anzeige nennt die tatsächlich geprüfte Bildzahl. Auf einen Vorschlag klicken, visuell die Motivzugehörigkeit prüfen und die volle Folge ausrichten.
2. Nach der Ausrichtung **Geeignete Öffnung suchen** wählen. Die Suche prüft Größen zwischen 20 und 100 Prozent und verschiebt die Öffnungsmitte begrenzt in Richtung besser abgedeckter Positionen. Danach die Vorschau berechnen.

## Qualitätsgrenzen

- Mindestens 60 Prozent der Bildfolge müssen ausgerichtet sein. Dies verhindert, dass die Synthese aus einem kleinen, zufällig verbleibenden Teil der Aufnahme entsteht.
- Mindestens 85 Prozent der Prüffläche müssen einen Blickpunkt innerhalb von 30 Prozent des Öffnungsradius erreichen (mindestens ein Analysepixel). Der größte Abstand darf 55 Prozent des Radius nicht überschreiten.
- Nicht abgedeckte Prüfzellen erhalten kein Gewicht. Sie werden nicht einer weit entfernten Aufnahme zugeschlagen.
- Nahe beieinanderliegende Aufnahmen teilen sich ein Positionsgewicht. Eine Position trägt höchstens zwölf Prozent. Mindestens neun effektive Positionen müssen übrig bleiben.
- Abdeckung, größtes Positionsgewicht und effektive Positionszahl werden beim Ergebnis angezeigt und in den Berechnungseinstellungen gespeichert.

Diese Grenzen sind konservative experimentelle Kriterien, keine optische Kalibrierung. Die tatsächliche gewichtete Öffnung kann trotz bestandener Prüfung von einem idealen Kreis abweichen. Gewichtskappung verändert ebenfalls die Öffnungsform. Eine bestandene lokale Merkmalsprüfung bestätigt keine globale Perspektivkorrektur.

## Prüfung mit den vorhandenen Flächenfolgen

Die fünf vorhandenen Ausrichtungsberichte wurden erneut geprüft. Für keinen wurde eine Flächenöffnung gefunden, die diese Grenzen erfüllt. Es wird daher kein angeblich verbessertes Bild aus den bestehenden großen Lücken erzeugt. Die alten Ergebnisse bleiben unverändert erhalten.

Für den bisherigen schmalen Schärfebereich mit 12/84 ausgerichteten Bildern liefert die Auswahlhilfe aus vorhandenen vollständigen Auswertungen unter anderem einen benachbarten Bereich mit 84/84 Bildern. Bei neuen Aufnahmen ohne solche Auswertungen ist die Siebenbild-Stichprobe nur eine Vorprüfung und kann durch größere Bewegungen auch scheitern. Vorschläge mit weniger als fünf erfolgreichen Stichprobenbildern werden nicht angeboten.

Eine KI-Tiefenkarte wird nicht verwendet. Aktuell stützt sich die Auswahl auf reale Bildkorrespondenzen und vorhandene Ausrichtungsberichte. Eine spätere Tiefenkarte könnte Vorschläge zusätzlich eingrenzen; sie würde keine fehlenden Blickpunkte ersetzen.

Zum Aktualisieren die laufende lokale Auswertung mit Strg+C schließen und `START_AUSWERTUNG.cmd` erneut öffnen. Die Aufnahme-PWA ist unverändert. Private Daten und Ergebnisse bleiben lokal.
