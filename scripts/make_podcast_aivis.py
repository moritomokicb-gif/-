"""AivisSpeech Engine で台本(A|せりふ / B|せりふ)を音声化して mp3 にする。
使い方: python3 make_podcast_aivis.py 台本.txt 出力.mp3 [話者ID_A,話者ID_B] [エンジンURL]
  事前に AivisSpeech Engine を起動しておくこと。同じフォルダの yomi.tsv を自動適用する。
  --check を付けると音声化せず、エンジンが解釈した読み(カタカナ)を行ごとに出力する。"""
import sys, os, io, json, time, subprocess, urllib.request, urllib.parse
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from yomi import load as _load, apply as _apply
    YOMI = _load()
except ImportError:
    YOMI, _apply = [], lambda t, _: t

args = [a for a in sys.argv[1:] if a != "--check"]
CHECK = "--check" in sys.argv
src = args[0]
out = args[1] if len(args) > 1 and not CHECK else None
ids = args[2] if len(args) > 2 else "888753760,1717361472"  # まお ノーマル / みちのくあいり 標準
URL = args[3] if len(args) > 3 else "http://127.0.0.1:10101"
SPK = dict(zip("AB", [int(x) for x in ids.split(",")]))

def post(path, params, body=None):
    req = urllib.request.Request(f"{URL}{path}?{urllib.parse.urlencode(params)}", method="POST",
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    for i in range(3):
        try:
            return urllib.request.urlopen(req, timeout=600).read()
        except Exception:
            if i == 2:
                raise
            time.sleep(5)

def reading(q):
    s = ""
    for ap in q["accent_phrases"]:
        s += "".join(m["text"] for m in ap["moras"])
        if ap.get("pause_mora"):
            s += "、"
    return s

lines = []
for n, line in enumerate(open(src, encoding="utf-8"), 1):
    line = line.strip()
    if "|" in line:
        who, text = line.split("|", 1)
        lines.append((n, who.strip(), _apply(text.strip(), YOMI)))

chunks, sr, t0 = [], 44100, time.time()
for i, (n, who, text) in enumerate(lines):
    spk = SPK.get(who, SPK["A"])
    q = json.loads(post("/audio_query", {"speaker": spk, "text": text}))
    if CHECK:
        print(f"{n}\t{text}\n\t{reading(q)}", flush=True)
        continue
    q["speedScale"] = 1.08
    q["postPhonemeLength"] = 0.2
    wav = post("/synthesis", {"speaker": spk}, q)
    x, sr = sf.read(io.BytesIO(wav), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    chunks += [x, np.zeros(int(sr * 0.25), dtype="float32")]
    if (i + 1) % 20 == 0:
        print(f"{i+1}/{len(lines)} lines, {time.time()-t0:.0f}s", flush=True)
if not CHECK:
    audio = np.concatenate(chunks)
    sf.write(out + ".wav", audio, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out + ".wav", "-af", "loudnorm",
                    "-ac", "1", "-ar", "44100", "-b:a", "64k", out], check=True)
    os.remove(out + ".wav")
    print(f"{len(audio)/sr/60:.1f} min, {time.time()-t0:.0f}s")
