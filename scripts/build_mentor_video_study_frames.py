from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
from yt_dlp import YoutubeDL


ROOT = Path(r"C:\Users\awind\OneDrive\문서\Trading")
OUTPUT_DIR = ROOT / "research" / "mentor-youtube" / "study_frames"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"
FORCE_REBUILD = {1, 16}

VIDEOS = [
    {
        "number": 1,
        "id": "6l3mktEl9PM",
        "title": "해외에서 이미 유명한 차트이론",
        "frames": [
            (194, "이전 고점의 유동성을 꼬리로 쓸어가는 장면"),
            (451, "Sweep 이후 구조 이탈과 OB 되돌림을 연결하는 장면"),
            (612, "반대편 손절 유동성을 TP 후보로 지정하는 장면"),
        ],
    },
    {
        "number": 2,
        "id": "7sQryLbDm6A",
        "title": "ICT트레이딩 진입 전략",
        "frames": [
            (260, "큰 시간봉에서 방향과 구조 이탈을 정하는 장면"),
            (332, "같은 위치를 작은 시간봉으로 세분화하는 장면"),
            (415, "LTF 전환 과정의 FVG에서 진입을 잡는 장면"),
        ],
    },
    {
        "number": 3,
        "id": "stffuxegJLk",
        "title": "FVG + liquidity 원리와 정리",
        "frames": [
            (514, "유동성 sweep 이후에도 즉시 진입하지 않는 장면"),
            (748, "FVG와 OB의 체결 범위 및 손절 위치를 비교하는 장면"),
            (822, "반대편 고점 유동성을 TP로 설정하는 장면"),
        ],
    },
    {
        "number": 4,
        "id": "PcufwRQn3zE",
        "title": "Price Action의 심리",
        "frames": [
            (226, "지지·저항 참가자들의 진입과 손절 위치를 추론하는 장면"),
            (396, "캔들 모양보다 손절이 몰린 가격대를 찾는 장면"),
            (513, "큰 흐름 뒤 작은 시간봉 전환을 기다리는 장면"),
        ],
    },
    {
        "number": 5,
        "id": "sZr8tlQEv7U",
        "title": "OB전략이 실패한 이유",
        "frames": [
            (221, "이미 체결되어 소진된 FVG·OB를 구분하는 장면"),
            (405, "현재 추세 속에서 되돌림 가능 범위를 판단하는 장면"),
            (515, "구조 전환과 OB 반응을 함께 확인하는 장면"),
        ],
    },
    {
        "number": 6,
        "id": "b9LzAMEu0JI",
        "title": "ICT시장 구조 가격대 판별",
        "frames": [
            (184, "Premium과 Discount로 후보 위치를 나누는 장면"),
            (397, "구조 변화 zone과 50% 위치를 함께 보는 장면"),
            (564, "FVG보다 OB를 선택한 실제 맥락을 설명하는 장면"),
        ],
    },
    {
        "number": 7,
        "id": "mcPF2iX1N-Y",
        "title": "15m ICT Trading",
        "frames": [
            (97, "FVG를 메우는 캔들과 OB 정의를 설명하는 장면"),
            (211, "저점 유동성 sweep과 하락 추세 OB를 연결하는 장면"),
            (292, "반대편 손절 유동성을 목표로 설정하는 장면"),
        ],
    },
    {
        "number": 8,
        "id": "KlECfDT1yas",
        "title": "실시간 트레이딩 2",
        "frames": [
            (93, "여러 시간봉에서 현재 상승 구조를 다시 점검하는 장면"),
            (208, "진입 이후 실제 유동성과 1차 목표를 재확인하는 장면"),
            (422, "과거 반응과 현재 시나리오를 동일시하지 않는 장면"),
        ],
    },
    {
        "number": 9,
        "id": "4J4YzAsrWbI",
        "title": "지금 진입 Yes or No",
        "frames": [
            (181, "H1의 불명확한 자리를 M15 OB로 세분화하는 장면"),
            (533, "외부 유동성과 내부 유동성을 구분하는 장면"),
            (781, "같은 가격을 다른 시간봉 구조로 다시 읽는 장면"),
        ],
    },
    {
        "number": 10,
        "id": "Q5vjDNLSNXM",
        "title": "진입 전략 1 Trend 확인",
        "frames": [
            (324, "FVG보다 시장 구조를 먼저 확인해야 하는 장면"),
            (581, "반대색 캔들 세 개로 구조 파동을 읽는 장면"),
            (823, "실제 구조 변화 이후 반대 방향을 고려하는 장면"),
        ],
    },
    {
        "number": 11,
        "id": "bCmYPKTj-pc",
        "title": "진입 전략 2 Liquidity 이용하기",
        "frames": [
            (338, "강하게 방어된 고저점 뒤 손절 유동성을 찾는 장면"),
            (516, "HTF 고저점과 LTF 구조 전환을 연결하는 장면"),
            (822, "계단식 추세의 FVG 되돌림을 진입에 쓰는 장면"),
        ],
    },
    {
        "number": 12,
        "id": "nFo44-vQUKE",
        "title": "진입 전략 3 FVG와 OB",
        "frames": [
            (331, "3캔들 FVG와 OB의 두 정의를 설명하는 장면"),
            (528, "큰 추세의 되돌림 속 LTF 반대 추세를 구분하는 장면"),
            (629, "반대편 손절 위치를 TP로 정하는 장면"),
        ],
    },
    {
        "number": 13,
        "id": "aFdHzpa9o48",
        "title": "진입 전략 4 Time frame 연동",
        "frames": [
            (294, "내부 구간에서 성급한 진입을 피하는 장면"),
            (621, "LTF CHoCH와 그 과정의 FVG·OB를 찾는 장면"),
            (1006, "지도·맥락·트리거 시간봉의 역할을 나누는 장면"),
        ],
    },
    {
        "number": 14,
        "id": "dD4PE-MlWmM",
        "title": "비트코인 실시간 트레이딩 매매 분석",
        "frames": [
            (347, "현재 거래 기간에 유효한 활성 추세를 고르는 장면"),
            (619, "다른 시간봉에서 구조와 FVG를 재확인하는 장면"),
            (799, "되돌림을 놓친 뒤 빠른 진입 조건을 검토하는 장면"),
        ],
    },
    {
        "number": 15,
        "id": "8cU6xdYaXaE",
        "title": "실패와 또 다른 기회",
        "frames": [
            (430, "BOS·BSL·M5 POI를 연결해 진입을 복기하는 장면"),
            (746, "OB 대기와 FVG 선반응의 차이를 비교하는 장면"),
            (1775, "낮은 승률과 높은 손익비의 관계를 설명하는 장면"),
        ],
    },
    {
        "number": 16,
        "id": "uhuyEbeJZP4",
        "title": "SMC ICT의 원리와 맥락 이해",
        "frames": [
            (556, "시장 구조 변화와 CHoCH 뒤 zone 반응을 읽는 장면"),
            (702, "LTF가 지저분할 때 HTF로 구조를 복원하는 장면"),
            (1265, "유동성 맥락이 있는 zone만 선별하는 장면"),
        ],
    },
    {
        "number": 17,
        "id": "iXOVCbwQh8A",
        "title": "가격이동 분석이 맞았나요",
        "frames": [
            (129, "외부 반전 미확정 상태에서 가까운 내부 TP를 고르는 장면"),
            (439, "중간 장애물과 OB에서 포지션을 관리하는 장면"),
            (572, "가격 전달 실패 시 다음 구조를 검토하는 장면"),
        ],
    },
    {
        "number": 18,
        "id": "7inzWhh_tdY",
        "title": "손절 기준과 재진입 시나리오",
        "frames": [
            (275, "첫 시나리오의 구조·유동성·목표를 복기하는 장면"),
            (482, "유사해 보이지만 후속 구조가 달라 손절된 장면"),
            (690, "새 방향 확인 후 재진입 시나리오를 세우는 장면"),
        ],
    },
    {
        "number": 19,
        "id": "x0duegy7hH8",
        "title": "SMC ICT 기준 매매일지 작성법",
        "frames": [
            (241, "진입 이유와 감정을 기록해 과매매 원인을 찾는 장면"),
            (388, "추세·유동성·공급 zone·trigger를 함께 복기하는 장면"),
            (567, "MTF 확인과 sniper 진입의 장단점을 비교하는 장면"),
        ],
    },
    {
        "number": 20,
        "id": "DARyWRgiN48",
        "title": "부담과 감사를 느낀 아서",
        "frames": [
            (292, "큰 구조에서 상승 추세를 먼저 확인하는 장면"),
            (361, "M30에 없던 OB를 M15에서 찾아내는 장면"),
            (469, "되돌림 하락 추세의 반전까지 기다리는 장면"),
        ],
    },
    {
        "number": 21,
        "id": "v2d-oOuu03s",
        "title": "실시간 트레이딩 빠르게 분석",
        "frames": [
            (121, "횡보 경계의 유동성과 OB를 연결하는 장면"),
            (510, "하락 추세 속 유동성·OB 반응으로 short를 검토하는 장면"),
            (657, "외부 상승과 내부 하락 구조를 분리하는 장면"),
        ],
    },
]


def format_time(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "malgunbd.ttf" if bold else "malgun.ttf"
    return ImageFont.truetype(str(Path(r"C:\Windows\Fonts") / filename), size=size)


def download_video(video_id: str, destination_dir: Path) -> Path:
    options = {
        "quiet": True,
        "no_warnings": True,
        "format": "18/best[ext=mp4][height<=480]/best[height<=480]",
        "outtmpl": str(destination_dir / "source.%(ext)s"),
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={video_id}", download=True
        )
        return Path(ydl.prepare_filename(info))


def extract_frame(ffmpeg: str, source: Path, seconds: int, destination: Path) -> None:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(seconds),
        "-i",
        str(source),
        "-frames:v",
        "1",
        "-vf",
        "scale=1280:-2",
        "-q:v",
        "2",
        "-y",
        str(destination),
    ]
    subprocess.run(command, check=True, timeout=90)


def fit_panel(image: Image.Image, width: int = 1280, height: int = 720) -> Image.Image:
    image = image.convert("RGB")
    scale = min(width / image.width, height / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    panel = Image.new("RGB", (width, height), "#0f1319")
    panel.paste(
        resized,
        ((width - resized.width) // 2, (height - resized.height) // 2),
    )
    return panel


def build_contact_sheet(video: dict, frame_paths: list[Path], destination: Path) -> None:
    width = 1280
    header_height = 108
    caption_height = 74
    panel_height = 720
    gap = 18
    total_height = (
        header_height
        + len(frame_paths) * (panel_height + caption_height)
        + (len(frame_paths) - 1) * gap
        + 20
    )
    sheet = Image.new("RGB", (width, total_height), "#0b0e13")
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(33, bold=True)
    caption_font = load_font(25, bold=True)
    sub_font = load_font(20)
    draw.text(
        (28, 20),
        f"{video['number']:02d}. {video['title']}",
        font=title_font,
        fill="#f3f5f7",
    )
    draw.text(
        (30, 68),
        "영상 프레임 기반 학습 장면",
        font=sub_font,
        fill="#8aa0b7",
    )

    y = header_height
    for frame_path, (seconds, caption) in zip(frame_paths, video["frames"]):
        panel = fit_panel(Image.open(frame_path))
        sheet.paste(panel, (0, y))
        y += panel_height
        draw.rectangle((0, y, width, y + caption_height), fill="#151b23")
        draw.text(
            (26, y + 20),
            f"{format_time(seconds)}  {caption}",
            font=caption_font,
            fill="#dce5ed",
        )
        y += caption_height + gap

    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, "JPEG", quality=88, optimize=True, progressive=True)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    manifest: list[dict] = []

    for video in VIDEOS:
        print(f"[{video['number']:02d}/21] {video['title']}", flush=True)
        destination = OUTPUT_DIR / f"{video['number']:02d}_{video['id']}_study.jpg"
        if not destination.exists() or video["number"] in FORCE_REBUILD:
            with tempfile.TemporaryDirectory(prefix=f"mentor-{video['number']:02d}-") as temp:
                temp_dir = Path(temp)
                source = download_video(video["id"], temp_dir)
                frames: list[Path] = []
                for index, (seconds, _) in enumerate(video["frames"], start=1):
                    frame_path = temp_dir / f"frame_{index}.jpg"
                    extract_frame(ffmpeg, source, seconds, frame_path)
                    frames.append(frame_path)
                build_contact_sheet(video, frames, destination)

        manifest.append(
            {
                "number": video["number"],
                "video_id": video["id"],
                "title": video["title"],
                "youtube_url": f"https://www.youtube.com/watch?v={video['id']}",
                "image": str(destination),
                "frames": [
                    {"seconds": seconds, "timestamp": format_time(seconds), "caption": caption}
                    for seconds, caption in video["frames"]
                ],
            }
        )

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Created {len(manifest)} study sheets in {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
