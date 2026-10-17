#!/usr/bin/env python3
"""Anlagenschema der SolvisRemote als Home-Assistant-Karte.

Die SolvisRemote zeigt auf schema.html das mit dem Solvis-Schema-Assistenten erzeugte Anlagenbild
(default.jpg, 950x550) und legt die Messwerte an den Positionen aus getPosition.xml darueber.
Dieses Werkzeug baut daraus eine picture-elements-Karte fuer Home Assistant mit den Entities des
SolvisSmartHomeServers (<domain>.solvis_<unit>_<kanal>) und erzeugt die Beschriftungsbilder der
Aktoren (grau = aus, gruen = an) im Stil der Remote.

Aufruf:
  anlagenschema.py --remote http://<ip> [--user solvis --password solvis] --unit SolvisMax --out ./schema
  anlagenschema.py --files <default.jpg> <getPosition.xml> --unit SolvisMax --out ./schema

Ergebnis im Ausgabeordner:
  schema.jpg, label_<id>_on.png / _off.png   -> nach /config/www/solvis/ kopieren
  anlagenschema.yaml                          -> Karte (type: picture-elements), ins Dashboard einfuegen
  preview.png (mit --preview key=wert ...)    -> Vorschau mit Beispielwerten

Die Koordinaten in getPosition.xml sind Seitenkoordinaten der Remote-Oberflaeche; relativ zum Bild
liegen die Kaestchen bei (x - 25, y - 90). Elemente mit x oder y < 0 sind in der Remote ausgeblendet.
"""
import argparse
import base64
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

IMG_W, IMG_H = 950, 550
OFF_X, OFF_Y = -25, -90
BOX_W, BOX_H = 98, 22          # 94x18 Inhalt + 2 px Rahmen
GREY, GREEN, BORDER, TEXT = (0xE6, 0xE6, 0xE6), (0xA0, 0xED, 0x80), (0x80, 0x80, 0x80), (0x70, 0x70, 0x70)
FONT_CANDIDATES = ['C:/Windows/Fonts/calibrib.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                   'C:/Windows/Fonts/DejaVuSans-Bold.ttf', 'C:/Windows/Fonts/arialbd.ttf']

# Aktoren A1/A2 liefert der Server als Drehzahl in Prozent, alle anderen als Schaltzustand.
PERCENT_ACTUATORS = {'A1', 'A2'}


def entity_for(item_id, unit):
    """Remote-Id (S1, A12, SL, RF1, P2) -> Entity-Id des SolvisSmartHomeServers."""
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


def label_image(text, fill, font):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (BOX_W, BOX_H), BORDER)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, BOX_W - 3, BOX_H - 3], fill=fill)
    d.text((5, 3), text, fill=TEXT, font=font)
    return im


def pct(v, total):
    return f'{v / total * 100:.2f}%'


BOX_STYLE = {
    'left': None, 'top': None, 'transform': 'none',
    'width': '94px', 'height': '18px', 'padding': '0 0 0 2px', 'box-sizing': 'content-box',
    'border': '2px solid #808080', 'background-color': '#E6E6E6', 'color': '#707070',
    'font-family': 'Calibri, "Segoe UI", Arial, sans-serif', 'font-size': '10pt', 'font-weight': 'bold',
    'line-height': '18px', 'text-align': 'left', 'white-space': 'nowrap', 'overflow': 'hidden',
}


def yaml_quote(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def build_yaml(items, unit, image_url, label_url_prefix):
    lines = ['# Anlagenschema der SolvisRemote als picture-elements-Karte, erzeugt von anlagenschema.py',
             f'# Unit {unit}; Bild und Beschriftungen liegen unter {image_url.rsplit("/", 1)[0]}/',
             'type: picture-elements', f'image: {image_url}', 'elements:']
    for it in items:
        ent = entity_for(it['id'], unit)
        if ent is None:
            continue
        left, top = pct(it['x'], IMG_W), pct(it['y'], IMG_H)
        if it['id'].startswith('A'):
            on_img = f'{label_url_prefix}label_{it["id"].lower()}_on.png'
            off_img = f'{label_url_prefix}label_{it["id"].lower()}_off.png'
            img_style = f'style: {{left: {left}, top: {top}, transform: none, width: {BOX_W}px}}'
            if it['id'] in PERCENT_ACTUATORS:
                # Drehzahl in Prozent: 0 = aus, alles andere = an
                off_states = '["0", "0.0", "unavailable", "unknown"]'
                lines.append(f'  # {it["id"]} {it["text"]} (Drehzahl)')
                for key, img in (('state_not', on_img), ('state', off_img)):
                    lines += ['  - type: conditional', '    conditions:',
                              '      - condition: state', f'        entity: {ent}',
                              f'        {key}: {off_states}',
                              '    elements:', '      - type: image', f'        entity: {ent}',
                              f'        image: {img}', '        tap_action: {action: more-info}',
                              f'        {img_style}']
            else:
                lines += [f'  # {it["id"]} {it["text"]}',
                          '  - type: image', f'    entity: {ent}', f'    image: {off_img}',
                          '    state_image:', f'      "on": {on_img}', f'      "off": {off_img}',
                          '    tap_action: {action: more-info}',
                          f'    style: {{left: {left}, top: {top}, transform: none, width: {BOX_W}px}}']
        else:
            style = dict(BOX_STYLE)
            style['left'], style['top'] = left, top
            style_yaml = ', '.join(f'{yaml_quote(k)}: {yaml_quote(v)}' for k, v in style.items())
            lines += [f'  # {it["id"]}', '  - type: state-label', f'    entity: {ent}',
                      f'    suffix: {yaml_quote(" " + it["text"])}',
                      f'    style: {{{style_yaml}}}']
    return '\n'.join(lines) + '\n'


def render_preview(image_bytes, items, unit, values, font, path):
    from PIL import Image, ImageDraw
    import io
    im = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    d = ImageDraw.Draw(im)
    for it in items:
        ent = entity_for(it['id'], unit)
        if ent is None:
            continue
        v = values.get(it['id'], '')
        if it['id'].startswith('A'):
            on = v not in ('', '0', '0.0', 'off', 'False', 'false')
            box = label_image(it['text'], GREEN if on else GREY, font)
            im.paste(box, (it['x'], it['y']))
        else:
            box = label_image(f'{v} {it["text"]}'.strip(), GREY, font)
            im.paste(box, (it['x'], it['y']))
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
    ap.add_argument('--www', default='/local/solvis/', help='URL-Pfad der Dateien in HA (Standard /local/solvis/)')
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

    font = load_font(13)
    for it in items:
        if it['id'].startswith('A'):
            label_image(it['text'], GREY, font).save(os.path.join(args.out, f'label_{it["id"].lower()}_off.png'))
            label_image(it['text'], GREEN, font).save(os.path.join(args.out, f'label_{it["id"].lower()}_on.png'))

    www = args.www if args.www.endswith('/') else args.www + '/'
    yaml_text = build_yaml(items, args.unit, www + 'schema.jpg', www)
    open(os.path.join(args.out, 'anlagenschema.yaml'), 'w', encoding='utf-8', newline='\n').write(yaml_text)

    if args.preview is not None:
        values = dict(kv.split('=', 1) for kv in args.preview)
        render_preview(image, items, args.unit, values, font, os.path.join(args.out, 'preview.png'))

    print(f'{len(items)} Elemente, Dateien in {args.out}:')
    for it in items:
        print(f'  {it["id"]:4s} {it["text"]:14s} ({it["x"]:3d},{it["y"]:3d}) -> {entity_for(it["id"], args.unit)}')


if __name__ == '__main__':
    main()
