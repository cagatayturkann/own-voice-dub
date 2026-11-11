"""Narrator read for own-voice-dub, run inside the VoxCPM2 studio's venv (voxcpm2-turkce-ses-tasarimi).

    <voxcpm2 venv python> vox_worker.py <voxcpm2 dir> <job.json> <out dir>

job.json: {"voice": "hazir/anlatici_en", "lang": "en", "lines": [{"id": "l001", "text": "..."}, ...]}
Every line is read in one engine session (model loaded once). A line the engine does not finish (no EOS) is read again
on its own with another seed, up to 3 times; the lines that did finish are kept, so one bad line never throws the rest
away. Writes <out dir>/<id>.wav (16-bit, engine sample rate) and <out dir>/result.json {"ok": [...], "failed": [...]}.
"""
import json
import sys
from pathlib import Path

import soundfile as sf


def main():
    studio, job_path, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
    sys.path.insert(0, str(studio))
    from ses_tasarim import ayarlar, motor, okunus

    settings = ayarlar.load(str(studio / "ayarlar.json"))
    job = json.loads(job_path.read_text(encoding="utf-8"))
    voice_dir = studio / "hazir_sesler" / job["voice"].split("/", 1)[1] if job["voice"].startswith("hazir/") \
        else Path(job["voice"])
    card = json.loads((voice_dir / "ses.json").read_text(encoding="utf-8"))
    seed = int(card["okuma_tohumu"])
    out.mkdir(parents=True, exist_ok=True)
    reference = motor.reference_wav(voice_dir / card.get("referans", "referans.wav"), out / "_motor")
    todo = {line["id"]: okunus.spoken(line["text"], job["lang"]).strip() for line in job["lines"]}
    done = []
    for attempt in range(4):  # first pass + 3 retries of the lines that did not finish
        if not todo:
            break
        requests = [motor.read_request(i, text, seed + attempt * 7919, reference, card["ses_yaratilirken_okutulan_metin"])
                    for i, text in todo.items()]
        print(f"okuma turu {attempt + 1}: {len(requests)} cümle", flush=True)
        result = motor.run_sequence(settings, requests, out / f"_motor{attempt}",
                                    lambda k, n, s: print(f"  {k}/{n} cümle, {s:.0f} sn", flush=True))
        for i, audio in result["audios"].items():
            sf.write(out / f"{i}.wav", audio, motor.SAMPLE_RATE)
            done.append(i)
            todo.pop(i)
        if todo:
            print(f"  bitmeyen cümleler: {sorted(todo)}; yeniden deneniyor", flush=True)
    (out / "result.json").write_text(json.dumps({"ok": sorted(done), "failed": sorted(todo)}), encoding="utf-8")
    print(f"bitti: {len(done)} cümle, bitmeyen {len(todo)}", flush=True)


if __name__ == "__main__":
    main()
