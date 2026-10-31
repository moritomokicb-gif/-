import sys, io, subprocess, numpy as np, soundfile as sf, pyopenjtalk
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
src, out = sys.argv[1], sys.argv[2]
ort = Onnxruntime.load_once(filename="voicevox_onnxruntime-linux-x64-1.23.2/lib/libvoicevox_onnxruntime.so.1.23.2")
syn = Synthesizer(ort, OpenJtalk(pyopenjtalk.OPEN_JTALK_DICT_DIR.decode()))
for f in ["4.vvm", "6.vvm"]:
    with VoiceModelFile.open(f"vvms/{f}") as m:
        syn.load_voice_model(m)
SPK = {"A": 11, "B": 30}  # 玄野武宏 ノーマル / No.7 アナウンス
chunks, sr = [], 24000
for line in open(src, encoding="utf-8"):
    line = line.strip()
    if "|" not in line:
        continue
    who, text = line.split("|", 1)
    q = syn.create_audio_query(text, SPK.get(who, 11))
    q.speed_scale = 1.1
    q.post_phoneme_length = 0.25
    x, sr = sf.read(io.BytesIO(syn.synthesis(q, SPK.get(who, 11))), dtype="float32")
    chunks += [x, np.zeros(int(sr * 0.2), dtype="float32")]
audio = np.concatenate(chunks)
sf.write(out + ".wav", audio, sr)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out + ".wav", "-af", "loudnorm",
                "-ac", "1", "-ar", "44100", "-b:a", "64k", out], check=True)
print(f"{len(audio)/sr/60:.1f} min")
