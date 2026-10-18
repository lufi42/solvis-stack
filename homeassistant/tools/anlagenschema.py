#!/usr/bin/env python3
"""Anlagenschema der SolvisRemote als Home-Assistant-Karte.

Die SolvisRemote zeigt auf schema.html das mit dem Solvis-Schema-Assistenten erzeugte Anlagenbild
(default.jpg, 950x550) und legt die Messwerte an den Positionen aus getPosition.xml darueber.
Dieses Werkzeug baut daraus eine Karte fuer Home Assistant mit den Entities des SolvisSmartHomeServers
bzw. solvis2mqtt (<domain>.solvis_<unit>_<kanal>):

  picture-elements mit dem Schema als Hintergrund und EINEM Overlay-Element, einem SVG, das die
  config-template-card (HACS, iantrich/config-template-card) aus den aktuellen Zustaenden erzeugt.
  SVG-Text und -Rahmen skalieren exakt mit dem Bild, bleiben scharf und folgen dem Dark Mode von HA.
  Hinweis: config-template-card wertet das Template per eval im Kontext der Karte aus; verfuegbar sind
  states, user, vars und this.hass (kein freies hass).

Aufruf:
  anlagenschema.py --remote http://<ip> [--user solvis --password solvis] --unit SolvisMax --out ./schema
  anlagenschema.py --files <default.jpg> <getPosition.xml> --unit SolvisMax --out ./schema

Ergebnis im Ausgabeordner:
  schema.jpg, schema_dark.jpg          -> nach /config/www/solvis/ kopieren
  anlagenschema.yaml                   -> Karte, ins Dashboard einfuegen (braucht config-template-card)
  preview.png (mit --preview ID=WERT)  -> Vorschau mit Beispielwerten

Die Koordinaten in getPosition.xml sind Seitenkoordinaten der Remote-Oberflaeche; relativ zum Bild
liegen die Kaestchen bei (x - 25, y - 90). Elemente mit x oder y < 0 sind in der Remote ausgeblendet.
"""
import argparse
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

IMG_W, IMG_H = 950, 550
OFF_X, OFF_Y = -25, -90
BOX_W, BOX_H = 98, 22          # 94x18 Inhalt + 2 px Rahmen, wie in der Remote
GREY, GREEN, BORDER, TEXT = (0xE6, 0xE6, 0xE6), (0xA0, 0xED, 0x80), (0x80, 0x80, 0x80), (0x70, 0x70, 0x70)
DARK_BG = (0x1C, 0x1C, 0x1C)   # Hintergrund der Dark-Mode-Variante des Bildes
FONT_CANDIDATES = ['C:/Windows/Fonts/calibrib.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                   'C:/Windows/Fonts/DejaVuSans-Bold.ttf', 'C:/Windows/Fonts/arialbd.ttf']

# Aktoren A1/A2 liefert der Server als Drehzahl in Prozent, alle anderen als Schaltzustand.
PERCENT_ACTUATORS = {'A1', 'A2'}


def entity_for(item_id, unit):
    """Remote-Id (S1, A12, SL, RF1, P2) -> Entity-Id des Servers."""
    u = unit.lower()
    m = re.fullmatch(r'([SA]|RF)(\d+)', item_id)
    if m:
        prefix, num = m.group(1), int(m.group(2))
        if prefix == 'S':
            return f'sensor.solvis_{u}_s{num:02d}'
        if prefix == 'A':
            domain = 'sensor' if item_id in PERCENT_ACTUATORS else 'binary_sensor'
            return f'{domain}.solvis_{u}_a{num:02d}'
        return f'sensor.solvis_{u}_rf{num}'
    m = re.fullmatch(r'P(\d+)', item_id)
    if m:
        return f'sensor.solvis_{u}_o_{m.group(1)}'
    if item_id in ('SL', 'SE'):
        return f'sensor.solvis_{u}_{item_id.lower()}'
    return None


def fetch(remote, path, user, password):
    mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    mgr.add_password(None, remote, user, password)
    opener = urllib.request.build_opener(urllib.request.HTTPDigestAuthHandler(mgr))
    with opener.open(remote.rstrip('/') + '/' + path, timeout=20) as r:
        return r.read()


def load_items(xml_bytes):
    root = ET.fromstring(xml_bytes.decode('utf-8-sig'))
    items = []
    for it in root.iter('item'):
        x, y = int(it.get('x').strip()), int(it.get('y').strip())
        if x < 0 or y < 0:
            continue
        items.append({'id': it.get('id').strip(), 'text': (it.get('text') or '').strip(),
                      'x': x + OFF_X, 'y': y + OFF_Y})
    return items


def load_font(size):
    from PIL import ImageFont
    for path in FONT_CANDIDATES:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_dark(image_bytes, min_area=25000):
    """Dark-Mode-Variante: grosse (fast) weisse Flaechen werden dunkel (Hintergrund, Innenraum der Rahmen),
    kleine weisse Flaechen (Badewanne, Heizkoerper, Symbole) bleiben weiss."""
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    w, h = im.size
    px = im.load()
    near = bytearray(w * h)       # 1 = weiss bis sehr hellgrau
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            lo = min(r, g, b)
            if lo >= 232 and max(r, g, b) - lo <= 12:
                near[y * w + x] = 1
    seen = bytearray(w * h)
    for start in range(w * h):
        if not near[start] or seen[start]:
            continue
        # zusammenhaengende Flaeche einsammeln (4er-Nachbarschaft)
        comp, stack = [], [start]
        seen[start] = 1
        while stack:
            i = stack.pop()
            comp.append(i)
            x, y = i % w, i // w
            for j in ((i - 1) if x > 0 else -1, (i + 1) if x < w - 1 else -1,
                      (i - w) if y > 0 else -1, (i + w) if y < h - 1 else -1):
                if j >= 0 and near[j] and not seen[j]:
                    seen[j] = 1
                    stack.append(j)
        if len(comp) < min_area:
            continue
        for i in comp:
            x, y = i % w, i // w
            r, g, b = px[x, y]
            k = (min(r, g, b) - 232) / 23.0   # weicher Uebergang an Kanten
            px[x, y] = tuple(int(c * (1 - k) + d * k) for c, d in zip((r, g, b), DARK_BG))
    out = io.BytesIO()
    im.save(out, 'JPEG', quality=92)
    return out.getvalue()


def js_array(rows):
    return '[' + ','.join('[%d,%d,%s,%s]' % (x, y, js_str(e), js_str(t)) for x, y, e, t in rows) + ']'


def js_str(s):
    return "'" + str(s).replace('\\', '\\\\').replace("'", "\\'") + "'"


def build_yaml(items, unit, image_url, dark_image_url):
    vals, acts, entities = [], [], []
    for it in items:
        ent = entity_for(it['id'], unit)
        if ent is None:
            continue
        entities.append(ent)
        if it['id'].startswith('A'):
            acts.append((it['x'], it['y'], ent, it['text']))
        else:
            vals.append((it['x'], it['y'], ent, it['text']))

    js = f"""${{ (() => {{
  const h = (typeof hass !== 'undefined') ? hass : this.hass;
  const dark = !!(h && h.themes && h.themes.darkMode);
  const bg = dark ? '#2e2e2e' : '#E6E6E6', bd = dark ? '#8a8a8a' : '#808080';
  const fg = dark ? '#d8d8d8' : '#707070', on = dark ? '#3c8a3c' : '#A0ED80';
  const fmt = (id) => {{
    const s = states[id];
    if (!s || s.state === 'unavailable' || s.state === 'unknown') return '–';
    const n = Number(s.state), u = s.attributes.unit_of_measurement || '';
    let t;
    if (isNaN(n)) t = s.state;
    else if (Math.abs(n) >= 1000 || Number.isInteger(n)) t = Math.round(n).toLocaleString('de-DE');
    else t = n.toFixed(1).replace('.', ',');
    return t + (u ? ' ' + u : '');
  }};
  const active = (id) => {{
    const s = states[id];
    return !!s && ['off', '0', '0.0', 'unavailable', 'unknown', 'false'].indexOf(s.state) < 0;
  }};
  const esc = (t) => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const vals = {js_array(vals)};
  const acts = {js_array(acts)};
  const box = (x, y, t, f) => '<rect x="' + (x + 1) + '" y="' + (y + 1) + '" width="{BOX_W - 2}" height="{BOX_H - 2}" fill="' + f + '" stroke="' + bd + '" stroke-width="2"/>'
    + '<text x="' + (x + 5) + '" y="' + (y + 15.5) + '" font-family="Calibri, Segoe UI, Arial, sans-serif" font-size="13" font-weight="bold" fill="' + fg + '">' + esc(t) + '</text>';
  let s = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {IMG_W} {IMG_H}" width="{IMG_W}" height="{IMG_H}">';
  for (const [x, y, e, l] of vals) s += box(x, y, fmt(e) + ' ' + l, bg);
  for (const [x, y, e, l] of acts) s += box(x, y, l, active(e) ? on : bg);
  s += '</svg>';
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(s);
}})() }}"""

    lines = ['# Anlagenschema der SolvisRemote, erzeugt von anlagenschema.py (solvis-stack).',
             f'# Unit {unit}. Braucht die HACS-Karte config-template-card; Bilder unter {image_url.rsplit("/", 1)[0]}/.',
             '# Das Overlay ist ein SVG mit Werten und Rahmen wie in der Remote, es skaliert mit dem Bild und folgt dem Dark Mode.',
             'type: custom:config-template-card', 'entities:']
    lines += [f'  - {e}' for e in entities]
    lines += ['card:', '  type: picture-elements', f'  image: {image_url}', f'  dark_mode_image: {dark_image_url}',
              '  elements:', '    - type: image', '      tap_action: {action: none}', '      hold_action: {action: none}',
              '      style: {left: 50%, top: 50%, width: 100%}', '      image: >-']
    lines += ['        ' + l for l in js.split('\n')]
    return '\n'.join(lines) + '\n'


def label_image(text, fill, font):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (BOX_W, BOX_H), BORDER)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, BOX_W - 3, BOX_H - 3], fill=fill)
    d.text((5, 3), text, fill=TEXT, font=font)
    return im


def render_preview(image_bytes, items, unit, values, font, path):
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    for it in items:
        ent = entity_for(it['id'], unit)
        if ent is None:
            continue
        v = values.get(it['id'], '')
        if it['id'].startswith('A'):
            on = v not in ('', '0', '0.0', 'off', 'False', 'false')
            im.paste(label_image(it['text'], GREEN if on else GREY, font), (it['x'], it['y']))
        else:
            im.paste(label_image(f'{v} {it["text"]}'.strip(), GREY, font), (it['x'], it['y']))
    im.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--remote', help='URL der SolvisRemote, z.B. http://192.168.1.50')
    src.add_argument('--files', nargs=2, metavar=('DEFAULT_JPG', 'GETPOSITION_XML'))
    ap.add_argument('--user', default='solvis')
    ap.add_argument('--password', default=os.environ.get('SOLVIS_PASSWORD', 'solvis'))
    ap.add_argument('--unit', required=True, help='Unit-Id aus der base.xml, z.B. SolvisMax')
    ap.add_argument('--out', required=True, help='Ausgabeordner')
    ap.add_argument('--www', default='/local/solvis/', help='URL-Pfad der Bilder in HA (Standard /local/solvis/)')
    ap.add_argument('--preview', nargs='*', metavar='ID=WERT', help='Vorschau mit Beispielwerten, z.B. S1=62.7°C A1=1')
    args = ap.parse_args()

    if args.remote:
        image = fetch(args.remote, 'default.jpg', args.user, args.password)
        positions = fetch(args.remote, 'getPosition.xml', args.user, args.password)
    else:
        image = open(args.files[0], 'rb').read()
        positions = open(args.files[1], 'rb').read()
    items = load_items(positions)
    os.makedirs(args.out, exist_ok=True)
    open(os.path.join(args.out, 'schema.jpg'), 'wb').write(image)
    open(os.path.join(args.out, 'schema_dark.jpg'), 'wb').write(make_dark(image))

    www = args.www if args.www.endswith('/') else args.www + '/'
    yaml_text = build_yaml(items, args.unit, www + 'schema.jpg', www + 'schema_dark.jpg')
    open(os.path.join(args.out, 'anlagenschema.yaml'), 'w', encoding='utf-8', newline='\n').write(yaml_text)

    if args.preview is not None:
        values = dict(kv.split('=', 1) for kv in args.preview)
        render_preview(image, items, args.unit, values, load_font(13), os.path.join(args.out, 'preview.png'))

    print(f'{len(items)} Elemente, Dateien in {args.out}:')
    for it in items:
        print(f'  {it["id"]:4s} {it["text"]:14s} ({it["x"]:3d},{it["y"]:3d}) -> {entity_for(it["id"], args.unit)}')


if __name__ == '__main__':
    main()
