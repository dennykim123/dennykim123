#!/usr/bin/env python3
"""주인님 사진 + README Empire 세계관 결합 아바타 생성.
사용: python3 combine_avatar.py <사진경로> [스타일: editorial|orb-companion]
"""
import sys, os, json, base64, mimetypes, urllib.request

PHOTO = sys.argv[1]
STYLE = sys.argv[2] if len(sys.argv) > 2 else "editorial"
OUT = os.path.expanduser("~/projects/dennykim123/assets/avatar-combined.png")

key = None
for line in open('/Volumes/blue/southbridge/.env.local'):
    if line.startswith('GSK_API_KEY='):
        key = line.strip().split('=', 1)[1]; break

mime = mimetypes.guess_type(PHOTO)[0] or "image/jpeg"
b64 = base64.b64encode(open(PHOTO, 'rb').read()).decode()
data_url = f"data:{mime};base64,{b64}"

PROMPTS = {
    # 실사 보존 + 세계관 조명: 얼굴은 사진 그대로, 골드 orb가 광원
    "editorial": (
        "Editorial portrait composite. Keep the person's face and likeness from the reference photo faithfully preserved and recognizable. "
        "Place them against a dark charcoal archive background with subtle towering stacks of ledgers out of focus. "
        "They are accompanied by a small warm golden glowing orb of light floating beside their shoulder, softly illuminating one side of their face with warm gold light. "
        "A faint glowing manuscript page drifts below the orb. Museum-poster matte grain, premium editorial lighting, dark and warm. "
        "Square avatar composition, subject centered, reads well at small sizes. No text, no typography."
    ),
    # 일러스트 변환: 세계관 화풍으로 초상 스타일라이즈
    "orb-companion": (
        "Stylized illustrated portrait in the style of a premium dark editorial illustration with warm golden accents. "
        "Transform the person from the reference photo into a hand-illustrated character while keeping their likeness clearly recognizable "
        "(face shape, hairstyle, glasses if any, expression). Matte grain texture, dark charcoal background, "
        "a small glowing golden orb creature carrying a tiny manuscript page floats beside them like a familiar. "
        "Square avatar composition, centered, strong silhouette at small sizes. No text, no typography."
    ),
}

body = {
    "query": PROMPTS[STYLE],
    "model": "nano-banana-pro",
    "aspect_ratio": "1:1",
    "image_size": "2k",
    "image_urls": [data_url],
}

sys.path.insert(0, '/Volumes/blue/southbridge/scripts')
import gsk_image
# gsk_image의 저수준 호출 재사용이 어려우면 직접 스트림 처리
req = urllib.request.Request(
    "https://www.genspark.ai/api/tool_cli/image_generation",
    data=json.dumps(body).encode(),
    headers={"X-Api-Key": key, "Content-Type": "application/json",
             "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"},
    method="POST")
urls = {"nowm": None, "wm": None}
with urllib.request.urlopen(req, timeout=300) as r:
    for line in r:
        line = line.strip()
        if not line: continue
        try: obj = json.loads(line)
        except json.JSONDecodeError: continue
        def walk(o):
            if isinstance(o, dict):
                if o.get("image_urls_nowatermark"): urls["nowm"] = urls["nowm"] or o["image_urls_nowatermark"]
                if o.get("image_urls"): urls["wm"] = urls["wm"] or o["image_urls"]
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(obj)

final = (urls["nowm"] or urls["wm"] or [None])[0]
assert final, "이미지 URL 없음"
# wrapper URL → download_url 교환
req2 = urllib.request.Request(
    "https://www.genspark.ai/api/tool_cli/file/download",
    data=json.dumps({"file_wrapper_url": final}).encode(),
    headers={"X-Api-Key": key, "Content-Type": "application/json",
             "User-Agent": "Mozilla/5.0 Chrome/124.0"},
    method="POST")
dl = json.loads(urllib.request.urlopen(req2, timeout=60).read())["data"]["download_url"]
open(OUT, "wb").write(urllib.request.urlopen(dl, timeout=120).read())
print("저장:", OUT, os.path.getsize(OUT), "bytes")
