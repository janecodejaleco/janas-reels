#!/usr/bin/env python3
"""Janas BTC: 5 narrated Reels per day from prewritten scripts. No AI API.

Usage: python gerar_reels.py --validate
       python gerar_reels.py --day 1 [--only pt] [--fake-tts] [--scenes 1]
Requires FFmpeg, Pillow and edge-tts. Edge TTS uses an online voice service.
"""
import argparse
import asyncio
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, features

ROOT = Path(__file__).resolve().parent
LANGS = {
    "pt": {"voice": "pt-BR-AntonioNeural", "label": "PORTUGUÊS", "cta": "SIGA PARA APRENDER"},
    "es": {"voice": "es-MX-JorgeNeural", "label": "ESPAÑOL", "cta": "SÍGUENOS PARA APRENDER"},
    "en": {"voice": "en-US-GuyNeural", "label": "ENGLISH", "cta": "FOLLOW TO LEARN"},
    "ru": {"voice": "ru-RU-DmitryNeural", "label": "РУССКИЙ", "cta": "ПОДПИШИСЬ И УЗНАВАЙ"},
    "he": {"voice": "he-IL-AvriNeural", "label": "עברית", "cta": "עקבו לעוד תוכן"},
}
WIDTH, HEIGHT = 720, 1280


def run(*args):
    p = subprocess.run([str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode:
        raise RuntimeError(f"Erro em {args[0]}: {p.stderr[-1600:]}")
    return p.stdout.strip()


def media_duration(p):
    return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", p))


HEADLINES = {
    "pt": ["", "ENTENDA", "COMO FUNCIONA", "O CUIDADO", "NA PRÁTICA"],
    "es": ["", "ENTIENDE", "CÓMO FUNCIONA", "ATENCIÓN", "EN LA PRÁCTICA"],
    "en": ["", "THE IDEA", "HOW IT WORKS", "THE RISK", "IN PRACTICE"],
    "ru": ["", "РАЗБЕРЁМСЯ", "КАК ЭТО РАБОТАЕТ", "ВАЖНО", "НА ПРАКТИКЕ"],
    "he": ["", "הרעיון", "איך זה עובד", "שימו לב", "בפועל"],
}
CAPTION_CTA = {
    "pt": "Mais uma aula curta sobre Bitcoin. Siga para acompanhar a série.",
    "es": "Otra lección corta sobre Bitcoin. Síguenos para continuar la serie.",
    "en": "One more short Bitcoin lesson. Follow for the next one.",
    "ru": "Ещё один короткий урок о биткоине. Подписывайтесь на продолжение.",
    "he": "עוד שיעור קצר על ביטקוין. עקבו כדי להמשיך בסדרה.",
}


def load_library():
    """Read complete human-authored multilingual scripts; fail if even one is missing."""
    source = ROOT / "roteiros_30_dias.txt"
    result = {}
    for lineno, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split("|", 3)
        if len(fields) != 4:
            raise ValueError(f"Linha {lineno}: esperado DIA|IDIOMA|TITULO|CENAS")
        number, lang, title, body = fields
        if not number.isdigit() or not 1 <= int(number) <= 30:
            raise ValueError(f"Linha {lineno}: dia fora de 1..30")
        day = int(number)
        if lang not in LANGS or not title.strip():
            raise ValueError(f"Linha {lineno}: idioma/título inválido")
        scenes = [x.strip() for x in body.split("~")]
        if len(scenes) != 5 or any(not x for x in scenes):
            raise ValueError(f"Linha {lineno}: exigidas cinco narrações completas")
        if (day, lang) in result:
            raise ValueError(f"Linha {lineno}: dia {day}, idioma {lang} duplicados")
        scene_objects = [{"headline": title if i == 0 else HEADLINES[lang][i], "narration": sentence} for i, sentence in enumerate(scenes)]
        caption = f"{title}\n\n{scenes[0]}\n\n{CAPTION_CTA[lang]}\n\n#Bitcoin #BTC #JanasBTC"
        result[day, lang] = {"title": title, "caption": caption, "scenes": scene_objects}
    missing = [(i, lang) for i in range(1, 31) for lang in LANGS if (i, lang) not in result]
    if missing:
        raise ValueError(f"Faltam scripts: {missing}")
    return result


def scheduled_day(target_date):
    start_str = os.getenv("DATA_INICIO", "2026-10-16")
    try:
        start = dt.date.fromisoformat(start_str)
    except ValueError as error:
        raise ValueError("DATA_INICIO deve estar no formato AAAA-MM-DD") from error
    if target_date < start:
        raise RuntimeError(f"Data anterior a {start}: configure DATA_INICIO ou use --day 1 para testar.")
    return ((target_date - start).days % 30) + 1


def validate(data):
    for lang in LANGS:
        v = data["videos"].get(lang)
        if not v or not v.get("title") or not v.get("caption") or len(v.get("scenes", [])) != 5:
            raise ValueError(f"Roteiro incompleto para {lang}")
    return data

def make_font(size, lang="en", heavy=False):
    candidates = []
    if lang == "he":
        candidates += ["/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf" if heavy else "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"]
    candidates += ["/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if heavy else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if heavy else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in candidates:
        if Path(path).exists(): return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def text_width(draw, line, font, rtl):
    opt = {"direction": "rtl"} if rtl and features.check("raqm") else {}
    box = draw.textbbox((0, 0), line, font=font, **opt)
    return box[2] - box[0]


def wrapped(draw, text, font, max_width, rtl):
    words = text.replace("\n", " ").split()
    rows, line = [], ""
    for word in words:
        probe = f"{line} {word}".strip()
        if text_width(draw, probe, font, rtl) > max_width and line:
            rows.append(line); line = word
        else: line = probe
    if line: rows.append(line)
    return rows


def draw_rtl_text(draw, xy, line, font, fill, rtl):
    extra = {"direction": "rtl"} if rtl and features.check("raqm") else {}
    draw.text(xy, line, font=font, fill=fill, **extra)


def render_card(filepath, title, scene, lang, i, day):
    rtl = lang == "he"
    img = Image.new("RGB", (WIDTH, HEIGHT), "#090F20")
    d = ImageDraw.Draw(img)
    # Vertical gradient, subtle fintech grid and original schematic network illustration.
    for y in range(HEIGHT):
        d.line((0, y, WIDTH, y), fill=(8 + y * 7 // HEIGHT, 15 + y * 12 // HEIGHT, 33 + y * 11 // HEIGHT))
    grid = (26, 44, 70)
    for x in range(20, WIDTH, 60): d.line([(x, 170), (x, 1110)], fill=grid, width=1)
    for y in range(190, 1110, 60): d.line([(20, y), (700, y)], fill=grid, width=1)
    # Accent band and gold typography.
    d.rounded_rectangle((44, 58, 675, 142), radius=23, fill="#182844")
    d.rounded_rectangle((45, 58, 53, 142), radius=4, fill="#F0B84C")
    brand = make_font(29, "en", True)
    d.text((78, 82), "JANAS BTC", font=brand, fill="#F9D388")
    badge = make_font(20, lang)
    label = LANGS[lang]["label"]
    w = text_width(d, label, badge, rtl)
    draw_rtl_text(d, (653 - w, 87), label, badge, "#BCCCE4", rtl)
    # Abstract peer-to-peer topology, not a fake price chart.
    seed = int(hashlib.sha256((lang + str(i) + day.isoformat()).encode()).hexdigest()[:12], 16)
    rng = random.Random(seed)
    cx, cy = 358, 725
    points = []
    for idx in range(8):
        angle = 2 * math.pi * idx / 8 + .12 * i
        radius = 150 + rng.randint(-32, 40)
        points.append((int(cx + radius * math.cos(angle)), int(cy + radius * math.sin(angle))))
    hub = (cx, cy)
    for idx, point in enumerate(points):
        nxt = points[(idx + 1) % len(points)]
        d.line([point, nxt], fill="#245169", width=4)
        if idx % 2 == 0:
            d.line([point, hub], fill="#2D7B89", width=5)
    for x, y in points:
        d.ellipse((x-10, y-10, x+10, y+10), fill="#F0BC5D")
    d.ellipse((cx-17, cy-17, cx+17, cy+17), fill="#84E0D1")
    # Slide number and rule.
    d.text((65, 205), f"{i+1:02d} / 05", font=make_font(30, "en", True), fill="#EFBF66")
    d.rounded_rectangle((64, 266, 656, 271), radius=2, fill="#364A68")
    d.rounded_rectangle((64, 266, 64 + (i + 1) * 592 // 5, 271), radius=2, fill="#F0B84C")
    # Main headline: large, short; natural text direction for Hebrew.
    headline = str(scene["headline"]).strip()
    mainfont = make_font(63, lang, True)
    lines = wrapped(d, headline, mainfont, 585, rtl)
    while (len(lines) > 4 or any(text_width(d, a, mainfont, rtl) > 585 for a in lines)) and mainfont.size > 36:
        mainfont = make_font(mainfont.size - 3, lang, True)
        lines = wrapped(d, headline, mainfont, 585, rtl)
    y = 347
    for line in lines:
        w = text_width(d, line, mainfont, rtl)
        x = (654 - w) if rtl else 65
        draw_rtl_text(d, (x, y), line, mainfont, "#F4F6FC", rtl)
        y += mainfont.size + 14
    # Bottom card is deliberately sparse: live subtitles will be burned in after encoding.
    d.rounded_rectangle((47, 962, 673, 1156), radius=26, fill="#15243B", outline="#324C69", width=2)
    subfont = make_font(28, lang, True)
    cta = LANGS[lang]["cta"]
    w = text_width(d, cta, subfont, rtl)
    draw_rtl_text(d, (max(78, 357-w/2), 908), cta, subfont, "#F4CF8D", rtl)
    footer = make_font(23, "en")
    d.text((65, 1194), "BITCOIN  /  EDUCATION", font=footer, fill="#93A7C4")
    d.text((554, 1194), day.strftime("%d.%m.%Y"), font=footer, fill="#93A7C4")
    img.save(filepath, optimize=True)


async def synthesize(txt, voice, dst, fake=False):
    if fake:
        duration = max(2.8, min(6.0, 1.6 + len(txt.split()) * 0.22))
        run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=24000", "-t", f"{duration:.3f}", "-c:a", "libmp3lame", "-q:a", "8", dst)
        return []
    import edge_tts
    events = []
    async def attempt():
        communicate = edge_tts.Communicate(txt, voice, rate="+0%", boundary="WordBoundary")
        with open(dst, "wb") as f:
            async for ch in communicate.stream():
                if ch["type"] == "audio": f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    events.append((ch["offset"] / 10_000_000.0, ch["duration"] / 10_000_000.0, ch["text"].strip()))
    for retry in range(3):
        try:
            await attempt()
            if not dst.exists() or dst.stat().st_size == 0: raise RuntimeError("Áudio vazio")
            return events
        except Exception:
            if retry == 2: raise
            events.clear()
            await asyncio.sleep(5 + 6 * retry)
    return events


def srt_time(sec):
    ms = max(0, int(round(sec * 1000)))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def subtitle_cues(events, narration, total):
    # Accurate word boundaries when supplied by Edge; approximate proportional timing otherwise.
    words = [(a, a + max(0.06, d), txt) for a, d, txt in events if txt.strip()]
    if not words:
        ws = narration.split()
        words = [(i * total / max(1, len(ws)), (i + 1) * total / max(1, len(ws)), w) for i, w in enumerate(ws)]
    result = []
    for i in range(0, len(words), 4):
        group = words[i:i+4]
        start = max(0, group[0][0] - .06)
        end = min(total + .1, max(group[-1][1], start + .25))
        result.append((start, end, " ".join(w[2] for w in group)))
    return result


def save_srt(entries, path):
    parts = []
    for i, (start, end, caption) in enumerate(entries, 1):
        parts += [str(i), f"{srt_time(start)} --> {srt_time(end)}", caption, ""]
    path.write_text("\n".join(parts), encoding="utf-8")


def scene_mp4(image_path, mp3, out, seconds):
    run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-framerate", "24", "-i", image_path, "-i", mp3,
        "-t", f"{seconds:.3f}", "-vf", "zoompan=z='min(zoom+0.00020,1.07)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=720x1280:fps=24,format=yuv420p",
        "-r", "24", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-c:a", "aac", "-b:a", "96k", "-ar", "48000", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out)


def burn_subs(input_path, srt_path, out):
    # Use simple UTF-8 filename, subtitle shaping provided by FFmpeg/libass and Noto fonts.
    filter_ = "subtitles=" + srt_path.name + ":force_style='FontName=Noto Sans,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,BackColour=&HAA0B1424,Alignment=2,MarginV=187'"
    run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", input_path.name, "-vf", filter_,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-c:a", "copy", "-movflags", "+faststart", out.name)


def produce_one(day, lang, script, outdir, fake=False, scenes_limit=None):
    p = outdir / lang
    p.mkdir(parents=True, exist_ok=True)
    pieces, subtitles, offset = [], [], 0.0
    scenes = script["scenes"][:scenes_limit] if scenes_limit else script["scenes"]
    for i, scene in enumerate(scenes):
        print(f"  {lang} {i+1}/{len(scenes)}: {scene['headline']}", flush=True)
        image = p / f"scene_{i+1:02d}.png"
        voice = p / f"audio_{i+1:02d}.mp3"
        video = p / f"clip_{i+1:02d}.mp4"
        render_card(image, script["title"], scene, lang, i, day)
        boundary = asyncio.run(synthesize(scene["narration"], LANGS[lang]["voice"], voice, fake))
        duration = media_duration(voice) + 0.15
        scene_mp4(image, voice, video, duration)
        real_duration = media_duration(video)
        for st, en, txt in subtitle_cues(boundary, scene["narration"], duration):
            subtitles.append((offset+st, min(offset+real_duration, offset+en), txt))
        offset += real_duration
        pieces.append(video)
    concat_file = p / "clips.txt"
    concat_file.write_text("\n".join(f"file '{x.name}'" for x in pieces), encoding="utf-8")
    joined = p / "joined.mp4"
    # FFmpeg relative-path concat requires cwd to be set to the clips directory.
    cp = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "clips.txt", "-c", "copy", "joined.mp4"], cwd=p, capture_output=True, text=True)
    if cp.returncode: raise RuntimeError("Erro ao unir cenas: " + cp.stderr[-1000:])
    srt = p / "subtitles.srt"
    save_srt(subtitles, srt)
    out = outdir / f"JANAS_BTC_{day.isoformat()}_{lang.upper()}.mp4"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", "joined.mp4", "-vf", "subtitles=subtitles.srt:force_style='FontName=Noto Sans,FontSize=11,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,BackColour=&H8A0B1424,Alignment=2,MarginV=43'", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26", "-c:a", "copy", "-movflags", "+faststart", str(out)]
    cp = subprocess.run(cmd, cwd=p, capture_output=True, text=True)
    if cp.returncode: raise RuntimeError("Erro ao incluir legendas: " + cp.stderr[-1600:])
    return out


def main():
    parser = argparse.ArgumentParser(description="Gerar cinco Reels diários sem usar Gemini ou API de IA")
    parser.add_argument("--validate", action="store_true", help="Confere os 150 roteiros; não produz vídeo")
    parser.add_argument("--day", type=int, default=0, help="Número de 1..30. Zero = seleção pela data e DATA_INICIO")
    parser.add_argument("--date", help="Data de saída AAAA-MM-DD (padrão: hoje em São Paulo)")
    parser.add_argument("--fake-tts", action="store_true", help="Somente teste técnico: substitui narração por silêncio")
    parser.add_argument("--only", choices=list(LANGS), help="Produz apenas um idioma")
    parser.add_argument("--scenes", type=int, choices=[1, 2, 3, 4, 5], default=5, help="Somente teste: limita quantidade de cenas")
    args = parser.parse_args()
    bank = load_library()
    if args.validate:
        print(f"VALIDADO: {len(bank)} roteiros, 30 dias, 5 idiomas, 5 cenas cada. Sem Gemini.")
        return
    if args.day not in range(0, 31):
        parser.error("--day deve estar entre 0 e 30")
    day = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    index = args.day or scheduled_day(day)
    scripts = {lang: bank[index, lang] for lang in LANGS}
    content = validate({"series_day": index, "topic": scripts["pt"]["title"], "videos": scripts})
    print(f"JANAS BTC | data {day.isoformat()} | aula {index}/30: {content['topic']}", flush=True)
    outdir = ROOT / "saida" / day.isoformat()
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "roteiros.json").write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    chosen = [args.only] if args.only else list(LANGS)
    captions = []
    for lang in chosen:
        outfile = produce_one(day, lang, scripts[lang], outdir, args.fake_tts, args.scenes)
        captions.extend([f"=== {lang.upper()} | {outfile.name} ===", scripts[lang]["caption"], ""])
        print(f"OK: {outfile}", flush=True)
    (outdir / "legendas_para_post.txt").write_text("\n".join(captions), encoding="utf-8")
    print(f"CONCLUÍDO: {len(chosen)} vídeos em {outdir}")
    if args.fake_tts:
        print("ATENÇÃO: áudio silencioso (--fake-tts). Os vídeos deste teste não devem ser publicados.")


if __name__ == "__main__":
    main()