"""読み替え表(TSV: 表記<TAB>読み)を台本に適用する。長い表記から先に置換する。"""
import os
DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yomi.tsv")
def load(path=None):
    path = path or DEFAULT
    rows = []
    if os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            l = l.rstrip("\n")
            if l and not l.startswith("#") and "\t" in l:
                k, v = l.split("\t", 1)
                rows.append((k, v))
    return sorted(rows, key=lambda r: -len(r[0]))
def apply(text, table):
    for k, v in table:
        text = text.replace(k, v)
    return text
