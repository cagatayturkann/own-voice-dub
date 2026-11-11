"""own-voice-dub: dub your own video into another language, in your own voice, on your own computer.

Two steps (run with the Chatterbox venv's python; see README.md):

    python dub.py prepare video.mp4 --from tr
        Writes video.dub.json: the video's sentences with their start/end times (Whisper). Then fill each
        sentence's target-language field ("en", "es", ...) with its translation (Claude Code does this: README).

    python dub.py run video.mp4 --voice my-voice.wav --lang en
        Writes video.en-dub.m4a (upload it in YouTube Studio -> Languages -> Dub) and video.en.srt.

What `run` does: separates the video's own voice from its music (Demucs) and keeps the music; a native narrator reads
each translated sentence (VoxCPM2, voxcpm2-turkce-ses-tasarimi); Chatterbox turns the narrator's voice into yours;
Whisper listens to every sentence and the key words must be heard, else it is converted again (3 tries); each
sentence is fitted into the original sentence's slot (pauses shrink, then up to 15% faster; a sentence that still
does not fit is reported: shorten its translation); every sentence is levelled, mixed over the music and the whole
track is matched to the video's loudness.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"  # {"voxcpm2_dir": "...", "voxcpm2_python": "...", "whisper_model": "..."}
NARRATORS = {"en": "hazir/anlatici_en", "es": "hazir/anlatici_es", "fr": "hazir/anlatici_fr", "de": "hazir/anlatici_de",
             "ru": "hazir/anlatici_ru", "ja": "hazir/anlatici_ja", "zh": "hazir/anlatici_zh"}
SR = 48000
CONTRACTIONS = {"it's": "it is", "there's": "there is", "that's": "that is", "you'll": "you will", "you're": "you are",
                "don't": "do not", "doesn't": "does not", "didn't": "did not", "isn't": "is not", "won't": "will not",
                "can't": "cannot", "i'm": "I am", "i've": "I have", "i'll": "I will", "we're": "we are",
                "let's": "let us", "what's": "what is", "here's": "here is", "they're": "they are"}
ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def log(msg):
    print(msg, flush=True)


def run(cmd, timeout, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=timeout, **kw)
    if r.returncode != 0:
        sys.exit(f"{Path(str(cmd[0])).name} failed ({r.returncode}): {(r.stderr or r.stdout)[-1200:]}")
    return r


def config():
    if not CONFIG.exists():
        sys.exit(f"missing {CONFIG}: copy config.example.json and fill in the paths (README, step 2)")
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], 60).stdout)


def loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=600)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else -23.0


# ---------- prepare ----------

def prepare(args):
    cfg = config()
    video = Path(args.video).resolve()
    work = video.parent / f".{video.stem}-dub"
    work.mkdir(exist_ok=True)
    wav = work / "speech16k.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", video, "-ac", "1", "-ar", "16000", wav], 600)
    run(["whisper-cli", "-m", cfg["whisper_model"], "-f", wav, "-l", args.source, "-ojf", "-of", work / "whisper",
         "-np"], 3600)
    segs = json.loads((work / "whisper.json").read_text(encoding="utf-8"))["transcription"]
    sentences, cur = [], None
    for s in segs:  # whisper segments -> sentences ending in . ? !
        text = s["text"].strip()
        if not text:
            continue
        t0, t1 = s["offsets"]["from"] / 1000, s["offsets"]["to"] / 1000
        if cur is None:
            cur = {"start": t0, "end": t1, "text": text}
        else:
            cur["end"], cur["text"] = t1, cur["text"] + " " + text
        if re.search(r"[.?!…]$", text):
            sentences.append(cur)
            cur = None
    if cur:
        sentences.append(cur)
    out = video.with_suffix(".dub.json")
    if out.exists() and not args.force:
        sys.exit(f"{out} exists (use --force to overwrite your translations)")
    out.write_text(json.dumps({"source": args.source, "sentences": [{"start": round(s["start"], 2), "end": round(s["end"], 2),
                   args.source: s["text"]} for s in sentences]}, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"{len(sentences)} sentences -> {out}\nNext: add the translation of each sentence as a new field (e.g. \"en\"); "
        f"keep each one no longer than the original when spoken (README: translation rules).")


# ---------- text ----------

def say_number(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else "-" + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + say_number(n % 100))
    for size, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= size:
            return say_number(n // size) + " " + name + ("" if n % size == 0 else " " + say_number(n % size))
    return str(n)


def clean(line, lang):
    """Text the narrator can read: English contractions and digits spelled out; other languages must spell numbers."""
    line = re.sub(r"\s*[;:]\s*", ", ", line.replace('"', "").replace("“", "").replace("”", "")).strip()
    if lang != "en":
        if re.search(r"\d", line):
            sys.exit(f"digit in a {lang} line, write the number as words: {line}")
        return line

    def expand(m):
        w = m.group(0)
        rep = CONTRACTIONS.get(w.lower())
        return w.replace("'", "").replace("’", "") if rep is None else (rep[0].upper() + rep[1:] if w[0].isupper() else rep)
    line = re.sub(r"[A-Za-z]+['’][A-Za-z]+", expand, line)
    line = re.sub(r"(\d+)%", lambda m: say_number(int(m.group(1))) + " percent", line)
    return re.sub(r"\d{1,3}(?:,\d{3})+|\d+", lambda m: say_number(int(m.group(0).replace(",", ""))), line)


def fold(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


NUMBER_WORDS = set(ONES + TENS[2:] + ["hundred", "thousand", "million", "billion", "percent"])


def key_words(text):
    words = [w for w in re.findall(r"[a-z]+", fold(text)) if len(w) >= 5 and w not in NUMBER_WORDS]
    return words or [w for w in re.findall(r"[a-z]+", fold(text)) if len(w) >= 3]


# ---------- run ----------

def separate(video, work):
    """Demucs: the video's music + effects without the voice (bed) and the voice alone (for its loudness)."""
    bed, voice = work / "bed.wav", work / "voice.wav"
    if bed.exists() and voice.exists():
        return bed, voice
    src = work / "orig.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", video, "-ac", "2", "-ar", "44100", src], 600)
    log("separating voice and music (Demucs)")
    run([sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs", "-o", work / "demucs", src], 7200)
    d = work / "demucs" / "htdemucs" / "orig"
    shutil.copy(d / "no_vocals.wav", bed)
    shutil.copy(d / "vocals.wav", voice)
    return bed, voice


def narrate(lines, lang, cfg, work):
    """Narrator read, cached per sentence text: after editing a translation only the changed sentences are read."""
    import hashlib
    cache = work / f"read-{lang}"
    cache.mkdir(parents=True, exist_ok=True)

    def key(t):
        return hashlib.sha1(f"{NARRATORS[lang]}|{t}".encode("utf-8")).hexdigest()[:12]
    todo = [t for t in dict.fromkeys(lines) if not (cache / f"{key(t)}.wav").exists()]
    if not todo:
        log("narrator read: cached")
    else:
        job_dir = work / "read-job"
        shutil.rmtree(job_dir, ignore_errors=True)
        job_dir.mkdir()
        job = {"voice": NARRATORS[lang], "lang": lang, "lines": [{"id": key(t), "text": t} for t in todo]}
        (job_dir / "job.json").write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
        log(f"narrator read: {len(todo)} of {len(lines)} sentences ({NARRATORS[lang]})")
        p = subprocess.Popen([cfg["voxcpm2_python"], str(HERE / "vox_worker.py"), cfg["voxcpm2_dir"],
                              str(job_dir / "job.json"), str(job_dir / "out")],
                             cwd=cfg["voxcpm2_dir"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            if "cümle" in line or "bitti" in line or "rror" in line:
                log("  " + line.strip())
        if p.wait(timeout=6 * 3600) != 0:
            sys.exit("narrator read failed (see above)")
        result = json.loads((job_dir / "out" / "result.json").read_text(encoding="utf-8"))
        for i in result["ok"]:
            shutil.move(str(job_dir / "out" / f"{i}.wav"), cache / f"{i}.wav")
        if result["failed"]:
            bad = [t for t in todo if key(t) in result["failed"]]
            sys.exit("the narrator could not finish these sentences; rephrase them (a little longer or shorter) and "
                     "run again:\n  " + "\n  ".join(bad))
    return [cache / f"{key(t)}.wav" for t in lines]


def convert(lines, reads, voice_ref, lang, cfg, work):
    """Chatterbox voice conversion to the user's voice + Whisper check, up to 3 tries per sentence (cached)."""
    import librosa
    import numpy as np
    import soundfile as sf
    import torch
    from chatterbox.vc import ChatterboxVC
    cache = work / f"vc-{lang}"
    cache.mkdir(exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    vc = None
    outs, report = [], []
    for n, (text, src) in enumerate(zip(lines, reads)):
        dst, meta = cache / f"{n:03d}.wav", cache / f"{n:03d}.json"
        if meta.exists() and json.loads(meta.read_text(encoding="utf-8"))["text"] == text:
            m = json.loads(meta.read_text(encoding="utf-8"))
        else:
            if vc is None:
                vc = ChatterboxVC.from_pretrained(device)
                vc.set_target_voice(str(voice_ref))
            need, best = key_words(text), None
            for attempt in range(3):
                w = vc.generate(str(src)).cpu().numpy()[0]
                tmp = cache / "_hear.wav"
                sf.write(tmp, librosa.resample(w, orig_sr=vc.sr, target_sr=16000), 16000)
                heard = run(["whisper-cli", "-m", cfg["whisper_model"], "-f", tmp, "-l", lang, "-np", "-nt"], 300).stdout.strip()
                got = sum(1 for q in need if q in fold(heard).replace("\u2019", "").replace("'", ""))
                if best is None or got > best[0]:
                    best = (got, w, heard, attempt + 1)
                if got == len(need):
                    break
            got, w, heard, tries = best
            sf.write(dst, w, vc.sr)
            m = {"text": text, "heard": heard, "ok": got == len(need), "tries": tries}
            meta.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        w, sr = sf.read(dst, dtype="float32")
        outs.append(librosa.resample(w, orig_sr=sr, target_sr=SR))
        report.append(f"{n + 1:3d} {'OK   ' if m['ok'] else 'CHECK'} try {m['tries']}: {m['heard']}")
        log(f"  converted {n + 1}/{len(lines)}")
    return outs, report


def level(w, target_db=-18.0):
    import numpy as np
    n = 1024
    if len(w) < n:
        return w
    rms = np.sqrt((w[: len(w) // n * n].reshape(-1, n) ** 2).mean(axis=1) + 1e-12)
    act = rms[20 * np.log10(rms) > -45]
    if not len(act):
        return w
    g = float(np.clip(target_db - 20 * np.log10(np.sqrt((act ** 2).mean())), -9, 9))
    return (w * 10 ** (g / 20)).astype("float32")


def atempo(w, tempo, work):
    import soundfile as sf
    if tempo <= 1.0005:
        return w
    a, b = work / "_t_in.wav", work / "_t_out.wav"
    sf.write(a, w, SR)
    run(["ffmpeg", "-y", "-v", "error", "-i", a, "-af", f"atempo={tempo:.4f}", b], 120)
    y, _ = sf.read(b, dtype="float32")
    return y


def place(blocks, parts, slots, total, max_tempo, work):
    import numpy as np
    track = np.zeros(int((total + 5) * SR), dtype=np.float32)
    rows, over, idx, cursor = [], [], 0, 0.0
    for n, (block, (start, nxt)) in enumerate(zip(blocks, slots)):
        ws = [level(w) for w in parts[idx: idx + len(block)]]
        idx += len(block)
        avail = nxt - start - 0.1
        speech = sum(len(w) for w in ws) / SR
        gap = 0.25 if speech + 0.25 * (len(ws) - 1) <= avail else 0.12
        sil = np.zeros(int(gap * SR), dtype=np.float32)
        y = np.concatenate([p for w in ws for p in (w, sil)][:-1])
        y = atempo(y, min(max(1.0, len(y) / SR / avail), max_tempo), work)
        at = max(start, cursor + 0.1)
        excess = len(y) / SR - avail
        if excess > 0.15:
            over.append((n + 1, round(excess, 2), " / ".join(block)))
        a = int(at * SR)
        y = y[: max(0, len(track) - a)]
        track[a: a + len(y)] += y
        cursor = at + len(y) / SR
        rows.append((at, cursor, " ".join(block)))
    return track[: int(total * SR)], rows, over


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def dub(args):
    import numpy as np
    import soundfile as sf
    cfg = config()
    t_start = time.time()
    video = Path(args.video).resolve()
    spec = json.loads(video.with_suffix(".dub.json").read_text(encoding="utf-8"))
    sents = spec["sentences"]
    missing = [i + 1 for i, s in enumerate(sents) if not s.get(args.lang, "").strip()]
    if missing:
        sys.exit(f"no '{args.lang}' translation for sentences {missing} in {video.with_suffix('.dub.json')}")
    if args.lang not in NARRATORS:
        sys.exit(f"no narrator for '{args.lang}': {', '.join(NARRATORS)}")
    work = video.parent / f".{video.stem}-dub"
    work.mkdir(exist_ok=True)
    total = duration(video)
    blocks = []
    for s in sents:  # split only at . ? ! : a 1-second piece on its own comes out garbled
        parts = [p.strip() for p in re.split(r"(?<=[.?!])\s+", s[args.lang]) if p.strip()]
        blocks.append([clean(p, args.lang) for p in parts])
    lines = [l for b in blocks for l in b]
    starts = [float(s["start"]) for s in sents]
    slots = [(starts[i], starts[i + 1] if i + 1 < len(starts) else total - 0.3) for i in range(len(starts))]

    bed, orig_voice = separate(video, work)
    reads = narrate(lines, args.lang, cfg, work)
    ref = work / "my-voice.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", Path(args.voice).resolve(), "-ac", "1", "-ar", "24000", ref], 120)
    parts, report = convert(lines, reads, ref, args.lang, cfg, work)
    voice, rows, over = place(blocks, parts, slots, total, args.max_tempo, work)
    vwav = work / f"voice-{args.lang}.wav"
    sf.write(vwav, voice, SR)

    target = min(-14.0, max(-16.0, loudness(video)))
    vgain = loudness(orig_voice) - loudness(vwav)
    mix = work / f"mix-{args.lang}.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", bed, "-i", vwav, "-filter_complex",
         f"[0:a]aresample={SR},aformat=channel_layouts=stereo[b];[1:a]volume={vgain:.2f}dB,aformat=channel_layouts=stereo[v];"
         f"[b][v]amix=inputs=2:duration=first:normalize=0,apad,atrim=0:{total:.3f}[m]", "-map", "[m]", "-ar", SR, mix], 600)
    out = video.with_name(f"{video.stem}.{args.lang}-dub.m4a")
    run(["ffmpeg", "-y", "-v", "error", "-i", mix, "-af",
         f"volume={target - loudness(mix):.2f}dB,alimiter=limit=0.891:level=false,atrim=0:{total:.3f}",
         "-c:a", "aac", "-b:a", "192k", "-ar", SR, out], 600)
    srt = video.with_name(f"{video.stem}.{args.lang}.srt")
    srt.write_text("".join(f"{i + 1}\n{srt_time(a)} --> {srt_time(b)}\n{s[args.lang].strip()}\n\n"
                           for i, (s, (a, b, _)) in enumerate(zip(sents, rows))), encoding="utf-8")
    log("\n".join(report))
    checks = sum(1 for r in report if " CHECK " in r)
    if checks:
        log(f"listen: Whisper missed a key word in {checks} sentence(s) (CHECK above); often only its spelling")
    for n, late, text in over:
        log(f"TOO LONG: sentence {n} by {late} s, shorten its translation: {text}")
    log(f"done in {time.time() - t_start:.0f} s -> {out}\n                -> {srt}")
    sys.exit(2 if over else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare", help="find the sentences and their times")
    p.add_argument("video")
    p.add_argument("--from", dest="source", default="tr", help="the video's language (default tr)")
    p.add_argument("--force", action="store_true")
    r = sub.add_parser("run", help="make the dub track")
    r.add_argument("video")
    r.add_argument("--voice", required=True, help="10-30 s of your own voice, wav/m4a/mp3")
    r.add_argument("--lang", default="en", help="target language: " + ", ".join(NARRATORS))
    r.add_argument("--max-tempo", type=float, default=1.15)
    args = ap.parse_args()
    prepare(args) if args.cmd == "prepare" else dub(args)


if __name__ == "__main__":
    main()
