# Smartochrome
Eine deutschsprachige PWA zum Prüfen von Smartphone-Kameras und Sammeln von Bildfolgen für eine **synthetische Öffnung**. Zielgerät des ersten Versuchs: Samsung Galaxy S22 Ultra mit Chrome. Die tatsächliche Unterstützung wird auf dem Gerät gemessen.

## Benutzung
1. GitHub-Pages-Adresse in Chrome öffnen, optional über das Browsermenü installieren.
2. **Kamera öffnen**, Rückkamera wählen. Ruhiges Motiv in hellem Licht, strukturierter Hintergrund in anderer Entfernung.
3. Im Livebild eine kleine, strukturierte Stelle auf dem Hauptmotiv antippen. Die gelbe Markierung ist der Schärfebereich für die spätere Ausrichtung. Die Größe ist einstellbar.
4. **A Stillhalten**, **B Seitlich bewegen** oder **C Fläche abtasten** wählen. Standard: acht Sekunden. B bewegt das Handy während der Aufnahme etwa 3 cm nach rechts. C führt in fünf Bahnen durch ein etwa 3 × 3 cm großes Quadrat. Handy parallel halten, nicht auf das Motiv einschwenken. Der gezeichnete Weg ist keine Messung.
5. **Countdown & Bildfolge starten** klicken. Drei Sekunden stillhalten. Erst bei **„Aufnahme läuft“** bewegen; für A weiter stillhalten. Einzelbilder werden automatisch gespeichert. Nach der Aufnahme erscheinen Vorschau, ZIP-Export und der nächste Vergleich direkt unter dem Livebild.
6. Alle drei ZIP-Dateien auf den Rechner übertragen. **Keine Aufnahmen ins öffentliche Repository hochladen.** Ein neuer Vergleichssatz bekommt eine eigene Kennung; bisherige Aufnahmen bleiben gespeichert.

Antippen steuert nicht den Hardware-Autofokus. Die Kameraeinstellungen werden in Version 0.2 nicht mehr manuell gesetzt: **„Einstellungen festhalten“ ist deaktiviert**, weil dieser Vorgang auf dem S22 Ultra zu dunklen Bildern führte. Der optionale Kameratest befindet sich unter „Kameraauswahl und Diagnose“ und erhält ebenfalls einen Countdown.

## Umfang der Version 0.2
- Kamera ohne Mikrofon, Gerätauswahl, gewünschte lange Kante 1280/1920 px und Anzeige der tatsächlichen Videoauflösung.
- Browserfähigkeiten, gemeldete Kameraeinstellungen und optionaler Bewegungssensor. Keine manuellen Eingriffe in Fokus, Belichtung oder Weißabgleich.
- Geführte Schritte, markierter Schärfebereich, Countdown und animierter Rasterweg. Der Aufnahmebericht enthält zusätzlich den normierten Bildbereich, Vergleichsreihenkennung und die ausdrücklich ungemessene Bewegungsvorgabe.
- JPEGs aus Videoframes ohne UI-Overlays; 8/12/20 gespeicherte Bilder/s angefragt. Kamera mit 30 Bildern/s angefragt. Tatsächlich gespeicherte Raten separat gemessen.
- `requestVideoFrameCallback` mit Framezeit und Präsentationszählung, soweit vorhanden. Fallback über Animationscallback und aktuelle Videozeit wird gekennzeichnet.
- Pro Bild: Zeitstempel, Einstellungen, JPEG-Kodierzeit, Helligkeit, Kontrast und Schärfeindikator. Das sind keine kalibrierten optischen Messwerte oder garantierten Sensorzeitstempel.
- Jedes akzeptierte Bild wird unmittelbar in IndexedDB gespeichert. Abbruch/Hintergrundwechsel und nach Neuladen erkannte unvollständige Sitzungen sind als Teilaufnahmen gekennzeichnet.
- Höchstens 180 Bilder und 48 MiB JPEG-Daten pro Folge. ZIP-Export benötigt zusätzlich temporären Speicher.
- Service Worker für Offline-Betrieb nach dem ersten vollständigen Laden. Browserdaten können vom System gelöscht werden: ZIPs separat sichern.
- Keine externen Bibliotheken, Schriften, Analyse-Endpunkte oder Foto-Uploads. App-Dateien kommen von GitHub Pages; Bilddaten bleiben lokal, bis der Nutzer sie selbst weitergibt.

## Bildsynthese
Die PWA ist das **Aufnahme- und Diagnosewerkzeug**. Die Synthese läuft separat auf dem Rechner: Ausrichtung auf eine Referenzebene, Gewichtung anhand relativer Parallaxe und Mittelung in linearem Licht. Die Autochromverarbeitung ist ein späterer Schritt.

Für einen ersten Versuch mit einer festen Schärfeebene ist eine vollständige Tiefenkarte nicht zwingend erforderlich. Alle Bildteile zur Deckung zu bringen würde die gewünschte Unschärfe entfernen. Horizontale Bewegung ergibt eine überwiegend horizontale synthetische Öffnung; rundere Unschärfe braucht Positionen über eine Fläche. Personenbewegung überlagert die räumliche Abtastung. Ein Server ist für die Datenerfassung nicht nötig; erste Synthese kontrolliert am Rechner.

## Lokale Oberfläche am Rechner

1. ZIPs in `Smartochrome/captures` ablegen. Vorhandene Versuche in `tests/Diagnosedateien` werden ebenfalls angezeigt.
2. Unter Windows **`START_AUSWERTUNG.cmd`** doppelklicken. Es öffnet sich `http://127.0.0.1:8024/` im Browser. Das Konsolenfenster während der Arbeit geöffnet lassen; Strg+C beendet den Dienst.
3. Eine Bildfolge auswählen. Im mittleren Bild einen kleinen Schärfebereich und einen strukturierten Bereich im weiter entfernten Hintergrund markieren. Klicken setzt ein Quadrat, Ziehen ein Rechteck; alternativ lassen sich Pixelkoordinaten eingeben. Die PWA-Markierung ist eine Vorschlagposition aus dem Livebild und muss am mittleren Bild geprüft werden.
4. **Bildfolge ausrichten**. Die erste Analyse kann einige Minuten dauern. Danach **Öffnungsgröße**, **Randgewichtung** und **Linien-/Flächenöffnung** wählen und die Vorschau berechnen.
5. **JPEG in voller Auflösung berechnen**, dann herunterladen. Ergebnisse, Transformationsdaten und Gewichtung stehen zusätzlich in `output/local-lab`.

Der lokale Dienst lauscht ausschließlich auf `127.0.0.1`. Dateien werden nicht an einen externen Dienst gesendet. Die PWA benötigt ihn nicht für die Aufnahme. NumPy und Pillow sind für die lokale Auswertung erforderlich; der Windows-Starter verwendet eine bereits vorhandene Codex-Python-Laufzeit, falls verfügbar. Auf anderen Rechnern einmal:

```powershell
python -m pip install -r requirements-lab.txt
python tools/local_lab.py
```

Die Ausrichtung arbeitet bis 1280 Pixel lange Kante, die Vorschau bis 640 Pixel; der JPEG-Export verwendet die ursprüngliche Auflösung. Die Flächenöffnung verwendet eine angenäherte kreisförmige Gewichtung in **relativen Bildkoordinaten**. Ein zu schmaler Aufnahmeweg wird abgelehnt. Das ist keine metrische Kalibrierung und kein Nachweis einer gleichmäßig gefüllten runden Öffnung. Bisherige reale Versuche sind horizontale Folgen; eine reale Rasterfolge steht noch aus. Öffnungslücken und Perspektivfehler können weiterhin Schlieren erzeugen. Die Wahl einer weicheren Gewichtung reduziert auch die effektive Öffnungsbreite.

Der Starter führt keine Downloads aus. Aufnahmen bleiben lokal; die Entwicklungsordner `captures`, `tests/Diagnosedateien`, `output` und Browserprofile sind von Git ausgeschlossen.

## Lokaler Syntheseprototyp für die Kommandozeile

`tools/synthetic_aperture.py` erzeugt einen ersten Vergleich aus einer ZIP-Bildfolge. Benötigt Python mit NumPy und Pillow. Der Bereich `--roi X Y BREITE HOEHE` bezeichnet ein strukturiertes, unbewegtes Motiv ungefähr in einer Schärfeebene; Koordinaten beziehen sich auf das mittlere Bild in voller Auflösung.

```powershell
python tools/synthetic_aperture.py captures/versuch.zip output/synthese --roi 300 510 110 190
python tests/test_synthetic_aperture.py
```

Der Prototyp schätzt pro Bild Verschiebung, Drehung und einheitliche Skalierung aus lokalen Bildkorrespondenzen. Er verwirft unzureichend passende Bilder und mittelt die übrigen in linearem Licht. `analysis.json` dokumentiert verwendete Bilder, Restfehler und Randbeschnitt; `reference.jpg` und `synthetic-aperture.jpg` haben denselben Beschnitt. `comparison.jpg` zeigt zusätzlich die unbeschnittenen Ansichten, deren äußere Ränder unterschiedlich viele Beiträge enthalten können.

Dies ist noch keine kalibrierte Öffnung: zeitliche Gleichgewichtung ersetzt keine räumliche Abtastung, horizontale Bewegung liefert gerichtete Unschärfe, und die einfache Ausrichtung kann zusätzliche Unschärfe verursachen. Die Auswertung läuft separat am Rechner; die PWA bleibt zunächst ein Aufnahmegerät. Private Aufnahmen und Ergebnisse bleiben außerhalb der Veröffentlichung.

### Verbesserte Auswertung mit Merkmalsverfolgung

`tools/refine_aperture.py` verfolgt Merkmale über benachbarte Bilder, prüft die Zuordnung rückwärts und verankert sie erneut im mittleren Bild. Ein **kleiner, strukturierter Schärfebereich auf einem Objekt** funktioniert besser als ein großer Bereich mit Vordergrund und sichtbarem Hintergrund. Es wird weiterhin nur eine gemeinsame Ähnlichkeitstransformation pro Aufnahme angewendet; der Hintergrund wird nicht separat ausgerichtet.

```powershell
python tools/refine_aperture.py captures/versuch.zip output/verbessert --roi 326 538 63 68 --background-roi 480 635 180 90 --baseline output/synthese/analysis.json
```

Die Verschiebung eines getrennten Hintergrundbereichs nach der Ausrichtung dient als **relative Parallaxenkoordinate**, nicht als metrische Kameraposition. Ähnliche Positionen teilen sich ein Gewicht; die Gewichte integrieren eine eindimensionale Öffnung über die Abstände zwischen Positionen. Voraussetzungen sind eine statische Szene und ein ungefähr gerader Aufnahmeweg. Der Bericht enthält die Abweichung von dieser Richtung sowie Lücken und Anzahl stabiler Hintergrundmerkmale.

Ausgaben mit identischem, vollständig abgedecktem Beschnitt:

- `reference.jpg`: mittleres Einzelbild.
- `baseline.jpg` / `matched.jpg`: alte und neue Ausrichtung mit exakt denselben gemeinsamen Bildern und gleichen Gewichten.
- `equal.jpg` / `uniform.jpg`: alle neu akzeptierten Bilder, einmal gleich pro Zeitpunkt und einmal räumlich ausgeglichen gewichtet.
- `tapered.jpg`: räumlicher Ausgleich plus weich auslaufende Cosinusgewichtung. Das reduziert auch die wirksame Öffnungsbreite.
- `registration.json` / `analysis.json`: Merkmalsprüfung, verwendete Bilder, Transformationen, relative Parallaxe und Gewichte.

`tools/build_aperture_report.py output/real-captures` baut für die beiden dort unter `refined-1` und `refined-2` abgelegten Versuche einen rein lokalen Vergleich. Die acht numerischen Tests laufen mit `python tests/test_synthetic_aperture.py`; sie enthalten auch eine künstliche Szene mit zwei Tiefen, in der die Schärfeebene erhalten und die Hintergrundparallaxe absichtlich nicht entfernt werden soll.

## Exportformat
`session.json`: Schema `smartochrome-capture/1`, Version, Aufnahmeweg, Motivnotiz, normalisierter Referenzpunkt im unbeschnittenen Bild, Soll-Einstellungen, Browserbericht, Frames und optionale IMU-Ereignisse. `frames/0000.jpg` usw. entsprechen der Reihenfolge im Manifest. Pro Frame: Zeitstempel, tatsächliche Abmessungen, Bytezahl, Kameraeinstellungen und Indikatoren.

Aufbereitete sRGB-Videobilder, **keine RAW-Dateien**. Geräte-IDs und Gruppenkennungen werden entfernt; keine Standortkoordinaten. Kamerabezeichnung und User-Agent bleiben zur Diagnose enthalten. IMU-Daten ergeben hier keine verlässlichen metrischen Kamerapositionen.

Mit Python ohne Zusatzpakete auf CRC, Vollständigkeit, JPEG-Abmessungen und Zeitstempel prüfen:
```powershell
python tools/inspect_capture.py captures/mein-versuch.zip
```

## Lokal prüfen
```powershell
npm.cmd run check
python tools/make_icons.py
python -m http.server 8023 --bind 127.0.0.1
```
`http://127.0.0.1:8023` auf demselben Rechner verwenden. Ein normales `http://192.168.…` auf dem Handy reicht nicht für die Kamera; dort die HTTPS-Pages-Adresse öffnen.

## GitHub Pages
Repository **Smartochrome**, Branch **main**, Quelle **/ (root)**. Settings → Pages → Deploy from a branch. Keine Build-Abhängigkeiten. Relative Pfade funktionieren unter `/Smartochrome/`.

Bei Änderungen Cache-Version in `sw.js` erhöhen. Ein bereitstehendes Update wird erst nach Auswahl aktiviert; eine laufende Aufnahme ist geschützt.

## Grenzen
Kein garantierter Zugriff auf alle Kameramodule, RAW, optische Stabilisierung, native Mehrkamera-Tiefendaten oder echte Belichtungsmetadaten. Browser und Betriebssystem bestimmen die verfügbaren Einstellungen. Desktoptests mit künstlichem Kamerastream ersetzen die Prüfung am S22 Ultra nicht.

## Grundlagen
- [W3C Image Capture](https://www.w3.org/TR/image-capture/)
- [Video-Frame-Callbacks](https://wicg.github.io/video-rvfc/)
- [Synthetische Öffnung](https://aperture.stanford.edu/courses/cs178-12/applets/dof.html)
- [GitHub Pages aus einem Branch](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
