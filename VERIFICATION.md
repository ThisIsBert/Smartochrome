# Prüfung · Smartochrome 0.2.0

Stand: 3. November 2026. Reale S22-Ultra-Bildfolgen aus Version 0.1 liegen lokal vor; ein realer Flächenversuch mit Version 0.2 steht noch aus.

## Version 0.2

- Neun Node-Tests und Syntaxprüfungen bestanden: bisherige ZIP-/Diagnoseprüfungen plus fünfzeilige Flächenbahn, stetiger Führungsverlauf, quadratischer und begrenzter Schärfebereich in Hoch-/Querformat.
- Zwölf Python-Tests bestanden: acht für Registrierung, Vorwärts-/Rückwärtsverfolgung, Ausreißer und Zweitiefenszene; vier für variable Öffnung, wiederholte Positionen, symmetrische Flächengewichtung und Ablehnung einer Linie als Flächenöffnung.
- Geführte Aufnahme mit künstlichem Kamerastream in Edge bei 412 px Breite geprüft: Aufnahme erst nach Markierung möglich; Festhalten der Kameraeinstellungen deaktiviert; Flächenmodus erzwingt mindestens acht Sekunden; Countdown und Aufnahmephase sichtbar verschieden.
- Vollständige achtsekündige Rasterfolgen gespeichert, Vorschau geöffnet und ZIP heruntergeladen (63 beziehungsweise 68 Bilder in zwei Durchläufen). Der ZIP-Prüfer bestätigte CRCs, Bildzahl, JPEG-Abmessungen und Zeitstempel. Normierter Schärfebereich, Vergleichsreihenkennung und nicht gemessene Rastervorgabe sind im Manifest enthalten. Keine manuellen Kamerasteuerungsversuche protokolliert.
- Abbruch während des Countdowns erzeugt keine zusätzliche Sitzung. „Weiter“ wählt den nächsten Vergleich ohne sofortige Aufnahme. Offline-Neuladen erhält App und gespeicherte Bildfolge. Kein horizontaler Überlauf bei 412 px, keine JavaScript-Seitenfehler, keine externen Foto-/Netzwerkanfragen im PWA-Test.
- Lokaler HTTP-Dienst mit einer realen 52-Bild-Folge geprüft: alle Bilder ausgerichtet; Vorschau mit zwei verschiedenen Öffnungen; JPEG-Export in Originalauflösung. Eine kleinere Öffnung verwendet weniger Blickpunkte. Unautorisierter Zugriff auf die private API liefert HTTP 403.
- Vollständiger Bedienweg der lokalen Oberfläche im Browser mit einer realen 52-Bild-Folge geprüft: Bereiche übernehmen, Ausrichtung starten, Öffnungsgröße und Randgewichtung ändern, Vorschau vergleichen und JPEG in voller Auflösung herunterladen. Eine Flächenöffnung für die horizontale Folge wird verständlich abgelehnt; danach bleibt die Linienöffnung bedienbar. Zu kleine Bereiche werden abgelehnt. Mobile und Desktopansichten wurden visuell geprüft; keine JavaScript-Seitenfehler.
- Programmcode wird über eine explizite Dateiliste veröffentlicht. Private ZIPs, Bilder, Auswertungen, Browserprofile und Testartefakte sind ausgeschlossen.

Die Browserprüfung verwendet einen künstlichen Kamerastream und ist keine neue Messung der Aufnahmeleistung auf dem S22 Ultra. Die bisherigen realen horizontalen Folgen liefern etwa 10–10,5 gespeicherte Bilder/s bei 720 × 1280 Pixeln. Die neue Rasterführung und deren optische Wirkung müssen noch am Gerät geprüft werden. Eine unkalibrierte Bildparallaxenkoordinate ist keine gemessene Kameraposition; die Gewichtung behauptet keine physikalische Blendenzahl.

## Vorherige Prüfung · Version 0.1.0

Stand: 3. November 2026. Noch keine reale Aufnahme auf dem Samsung S22 Ultra.

- Syntaxprüfung von app.js, core.js, storage.js und sw.js bestanden.
- Sechs Node-Tests bestanden: ZIP-Struktur/CRC, Standard-CRC32, gemessene Bildrate/Zeitlücken, konservative Beurteilung unvollständiger und langsamer Folgen, Entfernen von Gerätekennungen, Bildindikatoren.
- Headless Microsoft Edge mit künstlichem Kamerastream, mobile Breite 412 px und Desktop 1440 px; keine JavaScript-Seitenfehler.
- Kamerafreigabe, tatsächliche Auflösung, Einstellungsversuche und deren Rückmeldungen, Kameratest und Bildfolge über den regulären UI-Ablauf geprüft.
- JPEG-Kodierung bevorzugt über OffscreenCanvas.convertToBlob; Canvas.toBlob bleibt Fallback.
- Im Testbrowser bei 1280×720 bis ca. 7,5 gespeicherte Bilder/s, bei 1920×1080 ca. 3,7. Diese Messung ist keine Leistungsprognose für das S22 Ultra. Niedrige Bildraten werden als eingeschränkt ausgewiesen.
- ZIP-Download, Vorschau gespeicherter Bilder und Rückkehr zur Kamera geprüft.
- Abbruch lieferte eine gekennzeichnete Teilaufnahme. Neuladen während der Aufnahme stellte die bereits bestätigten Bilder wieder her und markierte den Versuch als unterbrochen.
- Offline-Neuladen nach Service-Worker-Installation erfolgreich. Bisherige Bildfolgen blieben verfügbar. App unter /Smartochrome/ geprüft, damit relative Pfade wie bei GitHub Pages funktionieren.
- Bei 412 px Viewport ebenfalls 412 px Dokumentbreite. Desktop- und Mobilansicht visuell geprüft.
- Während der Browserprüfung nur Anfragen an den lokalen Testserver und lokale Blob-URLs. Kein Foto-Upload, keine externen Bibliotheken.

Testartefakte liegen unter output/playwright und werden nicht ins Repository aufgenommen. Zu prüfen am echten Gerät: Kameramodule, manuelle Einstellungen, Bildrate, Verhalten im installierten PWA-Modus, Bilder unter realem Licht, Parallaxe und Schärfe. Geometrische Rekonstruktion und Synthese sind noch nicht Bestandteil dieser Version.

Zusätzlich: Python-ZIP-Prüfer bestätigte CRC, Bildzahl, JPEG-Abmessungen und Zeitstempel eines vollständigen Exports sowie einer nach Neuladen wiederhergestellten Teilaufnahme. Ein gezielt simulierter Speicherfehler nach dem ersten Bild erhielt genau das bereits gespeicherte Bild und erlaubte dessen Export.
