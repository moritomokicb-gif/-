"""台本の各行を音声合成エンジン(OpenJTalk)がどう読むかをカタカナで出力する。
使い方: python3 check_yomi.py 台本.txt [読み替え表.tsv] > yomi.txt
読み替え表を適用した後の読みを出すので、誤読があれば表に追加して再確認する。"""
import sys, pyopenjtalk
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from yomi import load, apply
table = load(sys.argv[2] if len(sys.argv) > 2 else None)
for i, line in enumerate(open(sys.argv[1], encoding="utf-8"), 1):
    if "|" not in line:
        continue
    text = apply(line.strip().split("|", 1)[1], table)
    print(f"{i}\t{text}\n\t{pyopenjtalk.g2p(text, kana=True)}")
