from __future__ import annotations

import json
import runpy
from pathlib import Path

from yt_dlp import YoutubeDL


ROOT = Path(r"C:\Users\awind\OneDrive\문서\Trading")
FRAME_SCRIPT = ROOT / "scripts" / "build_mentor_video_study_frames.py"
OUTPUT = (
    ROOT
    / "research"
    / "mentor-youtube"
    / "study_frames"
    / "notion_storyboards.json"
)


def pick_storyboard(info: dict) -> dict:
    storyboards = [
        item
        for item in info.get("formats", [])
        if item.get("ext") == "mhtml" and item.get("fragments")
    ]
    if not storyboards:
        raise RuntimeError(f"No storyboard found for {info.get('id')}")
    return max(
        storyboards,
        key=lambda item: (
            (item.get("width") or 0) * (item.get("height") or 0),
            item.get("rows") or 0,
            item.get("columns") or 0,
        ),
    )


def locate_tile(storyboard: dict, seconds: int) -> dict:
    fragments = storyboard["fragments"]
    rows = int(storyboard.get("rows") or 1)
    columns = int(storyboard.get("columns") or 1)
    cursor = 0.0
    selected_index = len(fragments) - 1
    selected_start = 0.0
    selected_duration = float(fragments[-1].get("duration") or 0.0)
    for index, fragment in enumerate(fragments):
        duration = float(fragment.get("duration") or 0.0)
        if seconds < cursor + duration or index == len(fragments) - 1:
            selected_index = index
            selected_start = cursor
            selected_duration = duration
            break
        cursor += duration

    cell_duration = selected_duration / max(rows * columns, 1)
    cell_index = min(
        int((seconds - selected_start) / max(cell_duration, 0.001)),
        rows * columns - 1,
    )
    return {
        "url": fragments[selected_index]["url"],
        "tile_index": selected_index,
        "tile_start": round(selected_start, 3),
        "tile_end": round(selected_start + selected_duration, 3),
        "cell_index": cell_index,
        "cell_row": cell_index // columns + 1,
        "cell_column": cell_index % columns + 1,
        "rows": rows,
        "columns": columns,
    }


def main() -> int:
    videos = runpy.run_path(str(FRAME_SCRIPT))["VIDEOS"]
    output: list[dict] = []
    options = {"quiet": True, "no_warnings": True, "skip_download": True}

    with YoutubeDL(options) as ydl:
        for video in videos:
            print(f"[{video['number']:02d}/21] {video['id']}", flush=True)
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video['id']}", download=False
            )
            storyboard = pick_storyboard(info)
            frames = []
            for seconds, caption in video["frames"]:
                frames.append(
                    {
                        "seconds": seconds,
                        "caption": caption,
                        **locate_tile(storyboard, seconds),
                    }
                )
            output.append(
                {
                    "number": video["number"],
                    "video_id": video["id"],
                    "title": video["title"],
                    "frames": frames,
                }
            )

    OUTPUT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
