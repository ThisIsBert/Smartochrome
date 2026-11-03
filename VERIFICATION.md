# Prüfung · Smartochrome 0.1.0

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
