"""Build a self-contained local comparison page from the two experiment reports."""
import argparse
import json
import statistics
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw


def build(root):
    summaries=[]
    for n in (1,2):
        folder=root/f'refined-{n}'; r=json.loads((folder/'analysis.json').read_text())
        accepted=[f for f in r['frames'] if 'transform' in f]
        summary={'sequence':n,'accepted':r['accepted'],'total':r['total'],'sameFrames':r['sameFramesComparisonCount'],
                 'holdout':statistics.median(f['holdoutMedianPx'] for f in accepted if f['holdoutMedianPx'] is not None),
                 'parallax':r['trajectory']['parallaxSpanPx'],'groups':r['weighting']['groups'],'crop':r['crop']}
        images={name:Image.open(folder/f'{name}.jpg').convert('RGB') for name in ('reference','baseline','matched','equal','uniform','tapered')}
        if len({img.size for img in images.values()})!=1: raise ValueError('Comparison image dimensions differ')
        x,y,w,h=r['roi']; margin=r['crop'][0]; box=(x-margin,y-margin,x+w-margin,y+h-margin)
        reference=np.asarray(images['reference'].crop(box).convert('L'),dtype=float).ravel()
        summary['focusCorrelation']={key:float(np.corrcoef(reference,np.asarray(images[key].crop(box).convert('L'),dtype=float).ravel())[0,1]) for key in ('baseline','matched')}
        labels=[('reference','Einzelbild'),('baseline','Erste Ausrichtung'),('matched','Neue Ausrichtung - gleiche Bilder'),('tapered','Neue Synthese - volle Folge, gewichtet')]
        # Detail comparison uses the same magnification and crop in every column.
        box=(max(0,x-margin-25),max(0,y-margin-25),min(images['reference'].width,x+w-margin+25),min(images['reference'].height,y+h-margin+25))
        tile_height=round((box[3]-box[1])*336/(box[2]-box[0]))
        tiles=[images[key].crop(box).resize((336,tile_height)) for key,_ in labels]
        panel=Image.new('RGB',(336*4,tile_height+44),'#1a1d1d'); draw=ImageDraw.Draw(panel)
        for j,((_,label),tile) in enumerate(zip(labels,tiles)):
            panel.paste(tile,(336*j,44)); draw.text((336*j+8,12),label,fill='white')
        panel.save(folder/'focus-comparison.jpg',quality=95)
        overview=Image.new('RGB',(360*3,720),'#1a1d1d'); draw=ImageDraw.Draw(overview)
        for j,(key,label) in enumerate([('reference','Einzelbild'),('baseline','Erste Ausrichtung'),('tapered','Neue Synthese')]):
            image=images[key].copy(); image.thumbnail((360,670)); overview.paste(image,(360*j+(360-image.width)//2,50)); draw.text((360*j+12,16),label,fill='white')
        overview.save(folder/'overview.jpg',quality=94)
        summaries.append(summary)
    controls=[]
    for n in (1,2):
        path=root/f'control-{n}/analysis.json'
        if path.exists():
            c=json.loads(path.read_text()); controls.append({'sequence':n,'sampled':len(c['sampledFrameIndices']),'accepted':c['accepted'],'parallax':c['trajectory']['parallaxSpanPx']})
    (root/'refined-summary.json').write_text(json.dumps({'sequences':summaries,'controls':controls},indent=2),encoding='utf-8')
    html='''<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Smartochrome – verbesserte Synthese</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{background:#191d1d;color:#edf2ef;font:17px system-ui;max-width:1100px;margin:28px auto;padding:0 18px}h1{font-size:clamp(24px,5vw,34px)}p{line-height:1.5;max-width:900px}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}label{display:grid;gap:6px}select,button{font:inherit;padding:10px;border:1px solid #85998e;border-radius:6px;background:#29312e;color:inherit}button{cursor:pointer}button:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid #b8dfca}a{color:#b8dfca}.viewer{position:relative;max-width:640px;margin:18px auto}.viewer img{width:100%;display:block}.viewer img:last-child{position:absolute;inset:0;clip-path:inset(0 0 0 50%)}.slider{max-width:640px;margin:auto;display:grid;gap:10px}.slider input{width:100%}.ends{display:flex;justify-content:space-between;gap:16px}.caption{background:#25312b;padding:14px;border-radius:6px}.detail{max-width:100%;height:auto}.small{font-size:15px;color:#c2cec6}table{border-collapse:collapse;width:100%;font-size:16px}td,th{padding:10px 8px;text-align:left;border-bottom:1px solid #536258}details{margin:24px 0}summary{cursor:pointer;font-weight:600}
.controls label{flex:1 1 300px;min-width:0;max-width:100%}.controls select{width:100%;min-width:0;max-width:100%}
</style></head><body>
<h1>Die nächste Fassung der synthetischen Öffnung</h1>
<p>Die große rosa Blüte ist jetzt der Schärfebereich. Die Aufnahmen werden auf diese Blüte ausgerichtet. Ihre räumlichen Unterschiede im übrigen Bild bleiben erhalten.</p>
<div class="controls"><label>Aufnahme<select id="sequence"><option value="1">Seitliche Folge 1</option><option value="2">Seitliche Folge 2</option></select></label>
<label>Vergleich<select id="mode"><option value="result">Einzelbild / neue Synthese</option><option value="alignment">Alte / neue Ausrichtung – dieselben Bilder</option><option value="density">Gleiche Zeitgewichte / räumlicher Ausgleich</option><option value="pupil">Gleichmäßige Öffnung / weich auslaufende Öffnung</option><option value="overall">Erste Fassung / neue Synthese</option></select></label></div>
<p id="stats"></p><p class="caption" id="explanation"></p>
<div class="slider"><div class="ends"><span id="leftLabel"></span><span id="rightLabel"></span></div><label for="split">Trennlinie verschieben<input id="split" type="range" min="0" max="100" value="50"></label><div class="ends"><button id="showLeft">Nur linkes Bild</button><button id="showRight">Nur rechtes Bild</button></div></div>
<div class="viewer"><img id="left" alt=""><img id="right" alt=""></div>
<details><summary>Blüte im Detail und Messwerte</summary><p>Die beiden mittleren Ausschnitte verwenden exakt dieselben Einzelbilder und Gewichte. Damit wird die neue Wahl und Ausrichtung des Schärfebereichs sichtbar. Die letzte Ansicht verwendet die vollständige akzeptierte Folge mit weicher Gewichtung.</p><img class="detail" id="detail" alt="Vier Vergleichsansichten der rosa Blüte"><p id="metrics"></p></details>
<details><summary>Was geändert wurde – und wo die Grenzen liegen</summary>
<p>Die Merkmale werden zwischen benachbarten Bildern verfolgt, rückwärts überprüft und erneut mit dem mittleren Bild verglichen. Pro Aufnahme wird weiterhin nur eine gemeinsame Transformation verwendet. Der Hintergrund wird nicht separat zur Deckung gebracht.</p>
<p>Die Verschiebung stabiler Hintergrundmerkmale gegenüber der Blüte dient als Näherung für die Aufnahmeposition. Nahe beieinanderliegende Positionen teilen sich ein Gewicht. Dadurch zählt kurzes Verharren nicht mehrfach wie eine zusätzliche Öffnungsfläche. Das sind keine vermessenen Kamerapositionen.</p>
<p>Die weich auslaufende Variante gewichtet die Ränder zusätzlich schwächer. Sie reduziert auch die wirksame Breite der Öffnung und damit die Unschärfe. Der Unterschied ist also nicht allein eine verbesserte Ausrichtung. Eine seitliche Folge bleibt eine längliche Öffnung; rundes Bokeh lässt sich daraus nicht rekonstruieren.</p>
<p>Andere Blüten und die Vase liegen nicht zwingend in derselben Schärfeebene. Restliche Perspektivfehler, Doppelkonturen und Streifen sind weiterhin möglich. Alle Ansichten eines Vergleichs haben denselben Beschnitt und vollständig abgedeckte Ränder.</p><p id="controls"></p></details>
<p class="small">Lokale Auswertung. Keine Fotos wurden hochgeladen. Die PWA wurde nicht geändert. <a href="AUSWERTUNG_V2.md">Auswertungsbericht</a> · <a href="VERGLEICH.html">Erste Versuchsfassung</a></p>
<script>
const data=__DATA__;
const modes={
 result:['reference','tapered','Einzelbild','Neue Synthese','Vollständige akzeptierte Bildfolge, räumlich ausgeglichen und zu den Rändern weich gewichtet.'],
 alignment:['baseline','matched','Erste Ausrichtung','Neue Ausrichtung','Identische Einzelbilder und gleiche Gewichte. Geändert sind die Auswahl der Referenzmerkmale und ihre Ausrichtung auf die rosa Blüte.'],
 density:['equal','uniform','Gleiche Gewichte pro Bild','Räumlicher Ausgleich','Dieselben Bilder und dieselbe Ausrichtung. Nur die Häufung ähnlicher Aufnahmepositionen wird ausgeglichen.'],
 pupil:['uniform','tapered','Gleichmäßige Öffnung','Weich auslaufende Öffnung','Gleiche Aufnahmen und gleicher räumlicher Ausgleich. Rechts zählen äußere Positionen weniger. Dadurch wird auch die wirksame Öffnung schmaler.'],
 overall:['baseline','tapered','Erste Fassung','Neue Synthese','Mehr Bilder, gezieltere Ausrichtung und andere Gewichte: Dieser Vergleich zeigt das Gesamtergebnis, nicht den isolierten Effekt einer einzelnen Änderung.']};
const el=id=>document.getElementById(id);
function update(){const n=Number(el('sequence').value),s=data.sequences[n-1],m=modes[el('mode').value];el('left').src=`refined-${n}/${m[0]}.jpg`;el('right').src=`refined-${n}/${m[1]}.jpg`;el('left').alt=m[2];el('right').alt=m[3];el('leftLabel').textContent=m[2];el('rightLabel').textContent=m[3];el('explanation').textContent=m[4];el('stats').textContent=`${s.accepted} von ${s.total} Bildern verwendet. Der reine Ausrichtungsvergleich verwendet ${s.sameFrames} gemeinsame Bilder.`;el('detail').src=`refined-${n}/focus-comparison.jpg`;el('metrics').textContent=`Median des Vorhersagefehlers an zurückgehaltenen Merkmalen der Blüte: ${s.holdout.toFixed(2)} Pixel. Gemessene relative Hintergrundverschiebung: ${s.parallax.toFixed(1)} Pixel. ${s.groups} Gruppen ähnlicher Positionen. Diese lokalen Messwerte sind keine globale Kalibrierung.`;}
function split(){el('right').style.clipPath=`inset(0 0 0 ${el('split').value}%)`;}
el('sequence').addEventListener('change',update);el('mode').addEventListener('change',update);el('split').addEventListener('input',split);
el('showLeft').addEventListener('click',()=>{el('split').value=100;split()});el('showRight').addEventListener('click',()=>{el('split').value=0;split()});
el('controls').textContent='Stillhalte-Kontrolle (je sieben Bilder über die Folge verteilt): '+data.controls.map(c=>`Folge ${c.sequence}: ${c.parallax.toFixed(1)} Pixel relative Hintergrundverschiebung`).join('; ')+'.';update();split();
</script></body></html>'''
    html=html.replace('__DATA__',json.dumps({'sequences':summaries,'controls':controls},ensure_ascii=False))
    (root/'VERGLEICH_V2.html').write_text(html,encoding='utf-8')
    print(json.dumps({'sequences':summaries,'controls':controls},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('root',type=Path)
    build(parser.parse_args().root)
