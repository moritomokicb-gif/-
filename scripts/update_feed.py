"""episodes/ の mp3 と見出しファイルから feed.xml と index.html を作り直す。

使い方: python3 scripts/update_feed.py <公開ディレクトリ> [保持日数] [番組キー]
  番組キー: brief(既定、モーニング・ブリーフ)/ run(ランニング・トーク。公開ディレクトリは site/run を渡す)
  公開ディレクトリには episodes/MorningBrief_YYYYMMDD.mp3 と
  episodes/MorningBrief_YYYYMMDD.txt(1行目=タイトル、2行目以降=見出し)を置く。
  保持日数(既定30)より古い回は削除する。
"""
import sys, os, glob, re, html, datetime, subprocess, hashlib
from email.utils import format_datetime

SHOWS = {
    "brief": dict(base="https://moritomokicb-gif.github.io/-", title="モーニング・ブリーフ", prefix="MorningBrief",
                  guid="morning-brief", hour=6, category="News",
                  desc="国内外のニュース、マーケット、製造業・FA、名古屋・岐阜の話題を毎朝お届けする個人用ニュース番組。音声:VOICEVOX:玄野武宏、VOICEVOX:No.7"),
    "run": dict(base="https://moritomokicb-gif.github.io/-/run", title="ランニング・トーク", prefix="RunTalk",
                guid="run-talk", hour=5, category="Technology",
                desc="テック・ガジェット、アニメ・サブカル、そしてニュースの裏側を考える約30分の個人用トーク番組。音声:VOICEVOX:玄野武宏、VOICEVOX:No.7"),
}
SHOW = SHOWS[sys.argv[3] if len(sys.argv) > 3 else "brief"]
BASE_URL, TITLE, DESC, PREFIX = SHOW["base"], SHOW["title"], SHOW["desc"], SHOW["prefix"]
JST = datetime.timezone(datetime.timedelta(hours=9))

root = sys.argv[1]
keep_days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
today = datetime.datetime.now(JST).date()

items = []
for mp3 in sorted(glob.glob(os.path.join(root, "episodes", f"{PREFIX}_*.mp3")), reverse=True):
    m = re.search(r"(\d{8})\.mp3$", mp3)
    if not m:
        continue
    d = datetime.datetime.strptime(m.group(1), "%Y%m%d").replace(tzinfo=JST)
    txt = mp3[:-4] + ".txt"
    if (today - d.date()).days > keep_days:
        os.remove(mp3)
        if os.path.exists(txt):
            os.remove(txt)
        continue
    lines = open(txt, encoding="utf-8").read().strip().splitlines() if os.path.exists(txt) else []
    title = lines[0] if lines else f"{d:%Y年%-m月%-d日}の{TITLE}"
    body = "\n".join(lines[1:])
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", mp3], capture_output=True, text=True).stdout.strip()
    secs = int(float(dur or 0))
    name = os.path.basename(mp3)
    h = hashlib.md5(open(mp3, "rb").read()).hexdigest()[:8]
    items.append(f"""    <item>
      <title>{html.escape(title)}</title>
      <description>{html.escape(body)}</description>
      <enclosure url="{BASE_URL}/episodes/{name}?v={h}" length="{os.path.getsize(mp3)}" type="audio/mpeg"/>
      <guid isPermaLink="false">{SHOW['guid']}-{m.group(1)}-{h}</guid>
      <pubDate>{format_datetime(d.replace(hour=SHOW["hour"]))}</pubDate>
      <itunes:duration>{secs}</itunes:duration>
    </item>""")

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{TITLE}</title>
    <link>{BASE_URL}/</link>
    <language>ja</language>
    <description>{html.escape(DESC)}</description>
    <itunes:author>{TITLE}</itunes:author>
    <itunes:image href="{BASE_URL}/cover.png"/>
    <itunes:category text="{SHOW['category']}"/>
    <itunes:explicit>false</itunes:explicit>
    <itunes:block>Yes</itunes:block>
{chr(10).join(items)}
  </channel>
</rss>
"""
open(os.path.join(root, "feed.xml"), "w", encoding="utf-8").write(feed)
open(os.path.join(root, "index.html"), "w", encoding="utf-8").write(
    f'<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex">'
    f'<title>{TITLE}</title><p>{TITLE}: <a href="feed.xml">feed.xml</a></p>')
print(f"{len(items)} episodes in feed")
