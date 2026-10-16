"""Minimal SolvisRemote GUI driver: screenshots and touches, same protocol as SolvisSmartHomeServer.
Usage: remote_gui.py <outdir> <step>[;<step>...]
  env: SOLVIS_REMOTE=http://<ip der SolvisRemote> (Pflicht), SOLVIS_USER/SOLVIS_PASSWORD (Standard solvis/solvis)
  steps: shot:NAME | touch:X,Y[,HOLD_MS[,WAIT_MS]] | back[:WAIT_MS] | wait:MS
Coordinates are display coordinates (240x128), doubled for Touch.CGI like the server does."""
import sys, time, os, random, urllib.request
from PIL import Image

BASE = os.environ.get("SOLVIS_REMOTE", "").rstrip("/")
if not BASE:
    sys.exit("SOLVIS_REMOTE nicht gesetzt, z.B. SOLVIS_REMOTE=http://192.168.1.50")
out = sys.argv[1]
os.makedirs(out, exist_ok=True)

pm = urllib.request.HTTPPasswordMgrWithDefaultRealm()
pm.add_password(None, BASE, os.environ.get("SOLVIS_USER", "solvis"), os.environ.get("SOLVIS_PASSWORD", "solvis"))
opener = urllib.request.build_opener(urllib.request.HTTPDigestAuthHandler(pm))

def get(path):
    with opener.open(BASE + path, timeout=15) as r:
        return r.read()

def shot(name):
    data = get("/display.bmp?")
    p = os.path.join(out, name + ".bmp")
    open(p, "wb").write(data)
    img = Image.open(p).convert("RGB")
    img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
    png = os.path.join(out, name + ".png")
    img.save(png)
    print("shot", png)

def touch(x, y, hold_ms=400, wait_ms=3500):
    get("/Touch.CGI?x=%d&y=%d" % (x * 2, y * 2))
    time.sleep(hold_ms / 1000)
    get("/Touch.CGI?x=520&y=520")  # release (260,260)*2
    time.sleep(wait_ms / 1000)
    print("touch", x, y, "hold", hold_ms)

def wake():
    """Touch an inert spot (screen title area) to end the screensaver, then wait."""
    get("/Touch.CGI?x=%d&y=%d" % (120 * 2, 5 * 2))
    time.sleep(0.4)
    get("/Touch.CGI?x=520&y=520")
    time.sleep(2.5)
    print("wake")

def back(wait_ms=3500):
    get("/Taster.CGI?taste=links&i=%d" % random.randint(0, 99999999))
    time.sleep(wait_ms / 1000)
    print("back")

for step in sys.argv[2].split(";"):
    step = step.strip()
    if not step:
        continue
    kind, _, arg = step.partition(":")
    if kind == "shot":
        shot(arg)
    elif kind == "touch":
        nums = [int(v) for v in arg.split(",")]
        touch(*nums)
    elif kind == "wake":
        wake()
    elif kind == "back":
        back(int(arg) if arg else 3500)
    elif kind == "wait":
        time.sleep(int(arg) / 1000)
    else:
        raise SystemExit("unknown step " + step)
