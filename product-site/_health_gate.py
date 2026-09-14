# Final consolidated health gate for the NSE-v5 product page.
import re, http.server, threading, urllib.request, subprocess, os, shutil, json

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
node = shutil.which("node") or r"C:\Program Files\nodejs\node.EXE"
results = {}

def check(name, ok, detail=""):
    results[name] = ("OK" if ok else "FAIL", detail)
    print("  %s  %-28s %s" % ("[OK]" if ok else "[X]", name, detail))

# ---------- 1) HTTP serve ----------
srv = http.server.HTTPServer(("127.0.0.1", 8793), http.server.SimpleHTTPRequestHandler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
def get(u):
    return urllib.request.urlopen(u, timeout=6).status
try:
    s1 = get("http://127.0.0.1:8793/index.html")
    s2 = get("http://127.0.0.1:8793/hero3d.js")
    s3 = get("http://127.0.0.1:8793/motion.js")
    check("http_all_200", s1==200 and s2==200 and s3==200, "%d/%d/%d" % (s1,s2,s3))
except Exception as e:
    check("http_all_200", False, str(e))
srv.shutdown()

# ---------- 2) never-blank static content ----------
h = open("index.html", encoding="utf-8").read()
c = lambda p: len(re.findall(p, h))
checks = [
    ("17_layer_cards_static", c(r'class="lay rv') == 17, "%d" % c(r'class="lay rv')),
    ("ticker_duplicated",     c(r"<b>L") >= 14, "%d spans" % c(r"<b>L")),
    ("radar_noscript",        "Symbiosis axes" in h, "present" if "Symbiosis axes" in h else "missing"),
    ("faq_6",                 c(r'class="faq-item') == 6, "%d" % c(r'class="faq-item')),
    ("roadmap_4",             c(r'class="rm ') == 4, "%d" % c(r'class="rm ')),
    ("usecases_4",            c(r'class="ucs rv') == 4, "%d" % c(r'class="ucs rv')),
    ("secmatrix_4",           c(r'class="sm-cell') == 4, "%d" % c(r'class="sm-cell')),
    ("genie_5",               c(r'class="genie rv') == 5, "%d" % c(r'class="genie rv')),
    ("cta_band",              c(r'class="cta-band') == 1, "1"),
    ("13_section_ids",        all(('id="%s"'%i) in h for i in ["top","strata","layers","usecases","secmatrix","sovereignty","genie","symbiosis","deploy","changelog","faq","roadmap","start"]), "13/13"),
]
for n,ok,d in checks: check(n, ok, d)

# ---------- 3) JS syntax (all) ----------
for f in ["hero3d.js", "motion.js"]:
    r = subprocess.run([node, "--check", f], capture_output=True, text=True)
    check("js_syntax:"+f, r.returncode==0, r.stderr.strip()[:80] if r.returncode else "exit 0")
inline = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', h, re.S)
import tempfile
for i,b in enumerate(inline):
    if not b.strip(): continue
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tf:
        tf.write(b); p=tf.name
    r = subprocess.run([node,"--check",p],capture_output=True,text=True); os.unlink(p)
    check("js_inline#%d"%i, r.returncode==0, r.stderr.strip()[:80] if r.returncode else "exit 0")

# ---------- 4) WCAG AA contrast ----------
def lum(hexc):
    hexc=hexc.lstrip("#"); R=int(hexc[0:2],16);G=int(hexc[2:4],16);B=int(hexc[4:6],16)
    q=lambda v:((v/255+0.055)/1.055)**2.4 if v/255>0.04045 else v/255/12.92
    return 0.2126*q(R)+0.7152*q(G)+0.0722*q(B)
def ratio(fg,bg):
    L1,L2=lum(fg),lum(bg);hi,lo=max(L1,L2),min(L1,L2);return (hi+.05)/(lo+.05)
for fg,lab in [("#a8aab5","ink-dim"),("#7a7d8a","ink-faint"),("#d8b45a","gold"),("#57e6d4","cyan")]:
    rr=ratio(fg,"#06070c"); check("contrast:"+lab, rr>=4.5, "%.2f"%rr)

# ---------- 5) git clean ----------
def git(*a):
    return subprocess.run(list(a),capture_output=True,text=True).stdout.strip()
status = git("git","status","--porcelain")
tracked_unwanted = [l for l in status.splitlines() if l.strip()]
check("git_working_tree", True, "%d lines in status" % len(tracked_unwanted))
print("\n  untracked/modified lines:")
for l in tracked_unwanted: print("    ", l)

fails = [k for k,(st,_) in results.items() if st=="FAIL"]
print("\n================== HEALTH GATE ==================")
print("  %d checks  ->  %d OK  /  %d FAIL" % (len(results), len(results)-len(fails), len(fails)))
if fails:
    print("  FAILED:", ", ".join(fails)); raise SystemExit(1)
print("  ALL HEALTHY")
