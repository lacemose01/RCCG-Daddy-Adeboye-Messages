import json
import math
import subprocess
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from urllib.parse import urlparse

from openpyxl import load_workbook


WORKBOOK = Path("Playlist.xlsx")
STATE = Path("station-playlist.json")
OUTPUT = Path("site/playlist.json")


def audio_duration(url):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", url],
        capture_output=True, text=True, timeout=120, check=True,
    )
    duration = float(result.stdout.strip())
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"Invalid audio duration for {url}")
    return duration


def read_tracks(path, known_durations):
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        rows = workbook.active.iter_rows(values_only=True)
        headers = next(rows, None)
        if not headers:
            raise ValueError("The Excel file is empty.")
        columns = {str(value).strip().lower(): i for i, value in enumerate(headers) if value is not None}
        if "title" not in columns or "cloudinary url" not in columns:
            raise ValueError("The first row must contain Title and Cloudinary Url columns.")
        tracks = []
        for row_number, row in enumerate(rows, start=2):
            if not any(value is not None and str(value).strip() for value in row):
                continue
            title = row[columns["title"]]
            url = row[columns["cloudinary url"]]
            if not isinstance(title, str) or not title.strip() or not isinstance(url, str):
                raise ValueError(f"Row {row_number} needs a title and Cloudinary URL.")
            url = url.strip()
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname != "res.cloudinary.com" or parsed.username or parsed.password:
                raise ValueError(f"Row {row_number} must contain a public HTTPS Cloudinary delivery URL.")
            speaker_index = columns.get("speaker")
            speaker = row[speaker_index] if speaker_index is not None else None
            duration = known_durations.get(url)
            if duration is None:
                print(f"Checking audio duration for row {row_number}...", flush=True)
                duration = audio_duration(url)
                known_durations[url] = duration
            tracks.append({
                "title": title.strip(),
                "speaker": str(speaker).strip() if speaker is not None and str(speaker).strip() else "Grace Radio",
                "url": url,
                "durationSeconds": duration,
            })
        if not tracks:
            raise ValueError("The Excel file contains no recordings.")
        return tracks
    finally:
        workbook.close()


def next_schedule_time(start, tracks, now):
    cycle = sum((Decimal(str(track["durationSeconds"])) for track in tracks), Decimal(0))
    if cycle <= 0:
        raise ValueError("The previous playlist has no valid duration.")
    earliest = max(now + timedelta(minutes=5), start + timedelta(seconds=float(cycle)))
    elapsed = Decimal(str((earliest - start).total_seconds()))
    cycles = (elapsed / cycle).to_integral_value(rounding=ROUND_CEILING)
    milliseconds = (cycles * cycle * 1000).to_integral_value(rounding=ROUND_CEILING)
    return start + timedelta(milliseconds=int(milliseconds))


def isoformat(value):
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def update_schedules(schedules, tracks, now):
    if not schedules:
        return [{"startAt": isoformat(now), "tracks": tracks}]
    parsed = [(datetime.fromisoformat(item["startAt"].replace("Z", "+00:00")), item) for item in schedules]
    if any(start.tzinfo is None for start, _ in parsed) or any(
        parsed[i][0] <= parsed[i - 1][0] for i in range(1, len(parsed))
    ):
        raise ValueError("Existing schedule times are invalid or not in order.")
    active = max((i for i, (start, _) in enumerate(parsed) if start <= now), default=0)
    schedules = [item for _, item in parsed[active:]]
    last_start, last = parsed[-1]
    if last["tracks"] != tracks:
        start = next_schedule_time(last_start, last["tracks"], now)
        schedules.append({"startAt": isoformat(start), "tracks": tracks})
    return schedules


def main():
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"schedules": []}
    schedules = state["schedules"]
    known_durations = {
        track["url"]: track["durationSeconds"]
        for schedule in schedules for track in schedule["tracks"]
    }
    tracks = read_tracks(WORKBOOK, known_durations)
    result = {"schedules": update_schedules(schedules, tracks, datetime.now(timezone.utc))}
    content = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    STATE.write_text(content, encoding="utf-8")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"Published {len(tracks)} tracks; latest schedule starts {result['schedules'][-1]['startAt']}.")


if __name__ == "__main__":
    main()
