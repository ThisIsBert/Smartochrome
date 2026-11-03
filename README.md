# Smartochrome
Eine deutschsprachige PWA zum Prüfen von Smartphone-Kameras und Sammeln von Bildfolgen für eine **synthetische Öffnung**. Zielgerät des ersten Versuchs: Samsung Galaxy S22 Ultra mit Chrome. Die tatsächliche Unterstützung wird auf dem Gerät gemessen.

## Benutzung
1. GitHub-Pages-Adresse in Chrome öffnen, optional über das Browsermenü installieren.
2. **Kamera öffnen**, Rückkamera wählen. Ruhiges Motiv in hellem Licht, strukturierter Hintergrund in anderer Entfernung.
3. **Einstellungen festhalten**: Fokus, Belichtung und Weißabgleich nur soweit vom Browser steuerbar. Akzeptierte, aber nicht zurückgemeldete Einstellungen gelten nicht als bestätigt.
4. **3-Sekunden-Kameratest**. Er misst tatsächlich gespeicherte Bilder, Bildrate, Lücken und grobe Helligkeit. Ein positives Resultat bestätigt noch keine räumliche oder optische Eignung.
5. Vergleichbare Versuche aufnehmen: **A Stillhalten**, **B seitlich**, **C Fläche**. Als erster Versuch ca. 5 cm Bewegung, Ausrichtung möglichst beibehalten. Die Anleitung misst keine Kamerapositionen.
6. Bildfolgen ansehen und als ZIP speichern. Diese ZIPs sowie die Diagnose-JSON gezielt zur Auswertung bereitstellen. **Keine Aufnahmen ins öffentliche Repository hochladen.**

Antippen im Livebild setzt einen Referenzpunkt für die spätere Ausrichtung, keinen Hardware-Autofokus. Der separate Fokusregler ist nur bei entsprechender Browserunterstützung steuerbar.

## Umfang der Version 0.1
- Kamera ohne Mikrofon, Gerätauswahl, gewünschte lange Kante 1280/1920 px und Anzeige der tatsächlichen Videoauflösung.
- Browserfähigkeiten, Kameraeinstellungen, dokumentierte Versuche zum Festhalten der Einstellungen, optionaler Bewegungssensor.
- JPEGs aus Videoframes ohne UI-Overlays; 8/12/20 gespeicherte Bilder/s angefragt. Kamera mit 30 Bildern/s angefragt. Tatsächlich gespeicherte Raten separat gemessen.
- `requestVideoFrameCallback` mit Framezeit und Präsentationszählung, soweit vorhanden. Fallback über Animationscallback und aktuelle Videozeit wird gekennzeichnet.
- Pro Bild: Zeitstempel, Einstellungen, JPEG-Kodierzeit, Helligkeit, Kontrast und Schärfeindikator. Das sind keine kalibrierten optischen Messwerte oder garantierten Sensorzeitstempel.
- Jedes akzeptierte Bild wird unmittelbar in IndexedDB gespeichert. Abbruch/Hintergrundwechsel und nach Neuladen erkannte unvollständige Sitzungen sind als Teilaufnahmen gekennzeichnet.
- Höchstens 180 Bilder und 48 MiB JPEG-Daten pro Folge. ZIP-Export benötigt zusätzlich temporären Speicher.
- Service Worker für Offline-Betrieb nach dem ersten vollständigen Laden. Browserdaten können vom System gelöscht werden: ZIPs separat sichern.
- Keine externen Bibliotheken, Schriften, Analyse-Endpunkte oder Foto-Uploads. App-Dateien kommen von GitHub Pages; Bilddaten bleiben lokal, bis der Nutzer sie selbst weitergibt.

## Bildsynthese
Version 0.1 ist das **Aufnahme- und Diagnosewerkzeug**, noch kein fertiger Synthesizer. Zuerst werden reale Bildfolgen auf Zeitlücken, wechselnde Belichtung, Bildschärfe, Rotation und Parallaxe untersucht. Danach folgen Ausrichtung auf eine Referenzebene, räumliche Gewichtung der Kamerapositionen und Mittelung in angenähert linearem Licht, anschließend die Autochromverarbeitung.

Für einen ersten Versuch mit einer festen Schärfeebene ist eine vollständige Tiefenkarte nicht zwingend erforderlich. Alle Bildteile zur Deckung zu bringen würde die gewünschte Unschärfe entfernen. Horizontale Bewegung ergibt eine überwiegend horizontale synthetische Öffnung; rundere Unschärfe braucht Positionen über eine Fläche. Personenbewegung überlagert die räumliche Abtastung. Ein Server ist für die Datenerfassung nicht nötig; erste Synthese kontrolliert am Rechner.

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
