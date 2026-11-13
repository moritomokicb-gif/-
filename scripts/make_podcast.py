import sys, io, os, subprocess, numpy as np, soundfile as sf, pyopenjtalk
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from yomi import load as _load_yomi, apply as _apply_yomi
    YOMI = _load_yomi()
except ImportError:
    YOMI, _apply_yomi = [], lambda t, _: t
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
# 使い方: make_podcast.py 台本 出力mp3 [vvmファイル(カンマ区切り)] [話者ID A,B]
# 例(ランニング・トーク): make_podcast.py s.txt o.mp3 0.vvm,1.vvm 8,14
src, out = sys.argv[1], sys.argv[2]
VVMS = sys.argv[3].split(",") if len(sys.argv) > 3 else ["4.vvm", "6.vvm"]
SPK_IDS = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else [11, 30]
ort = Onnxruntime.load_once(filename="voicevox_onnxruntime-linux-x64-1.23.2/lib/libvoicevox_onnxruntime.so.1.23.2")
syn = Synthesizer(ort, OpenJtalk(pyopenjtalk.OPEN_JTALK_DICT_DIR.decode()))
for f in VVMS:
    with VoiceModelFile.open(f"vvms/{f}") as m:
        syn.load_voice_model(m)
SPK = {"A": SPK_IDS[0], "B": SPK_IDS[1]}  # 既定: 玄野武宏 ノーマル / No.7 アナウンス
chunks, sr = [], 24000
for line in open(src, encoding="utf-8"):
    line = line.strip()
    if "|" not in line:
        continue
    who, text = line.split("|", 1)
    text = _apply_yomi(text, YOMI)
    q = syn.create_audio_query(text, SPK.get(who, SPK_IDS[0]))
    q.speed_scale = 1.1
    q.post_phoneme_length = 0.25
    x, sr = sf.read(io.BytesIO(syn.synthesis(q, SPK.get(who, SPK_IDS[0]))), dtype="float32")
    chunks += [x, np.zeros(int(sr * 0.2), dtype="float32")]
audio = np.concatenate(chunks)
sf.write(out + ".wav", audio, sr)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out + ".wav", "-af", "loudnorm",
                "-ac", "1", "-ar", "44100", "-b:a", "64k", out], check=True)
print(f"{len(audio)/sr/60:.1f} min")
