# -*- coding: utf-8 -*-
"""
Находит видео в кодеках, которые НЕ играет браузер (hap, prores, hevc/h265, dnxhd …)
и перекодирует их в веб-совместимый H.264/AAC .mp4 (+faststart) рядом с оригиналом.

Оригинал не удаляется. gen_data.py игнорирует исходник, если рядом есть .mp4 с тем же именем.

Запуск:  py webify_videos.py
Нужен ffmpeg/ffprobe (ищется в PATH или в установке winget).
"""
import os, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
VID_EXT = {".mp4", ".mov", ".webm", ".m4v", ".avi", ".mkv"}
SKIP_DIRS = {"posters", "deploy", "__pycache__"}

# кодеки, которые браузер играет без проблем
WEB_SAFE = {"h264", "vp8", "vp9", "av1"}


def find_tool(name):
    exe = shutil.which(name)
    if exe:
        return exe
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages")
    for dp, _, files in os.walk(base):
        if name + ".exe" in files:
            return os.path.join(dp, name + ".exe")
    return None


def codec_of(ffprobe, path):
    r = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name", "-of", "csv=p=0", path],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return r.stdout.decode("utf-8", "ignore").strip()


def main():
    ff, fp = find_tool("ffmpeg"), find_tool("ffprobe")
    if not ff or not fp:
        print("ffmpeg/ffprobe не найдены. Установи: winget install Gyan.FFmpeg")
        sys.exit(1)

    todo = []
    for dp, dirnames, files in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in VID_EXT:
                continue
            full = os.path.join(dp, fn)
            codec = codec_of(fp, full)
            if codec and codec not in WEB_SAFE:
                todo.append((full, codec))

    if not todo:
        print("Все видео уже в веб-совместимых кодеках. Конвертировать нечего.")
        return

    print(f"Несовместимых роликов: {len(todo)}")
    for full, codec in todo:
        out = os.path.splitext(full)[0] + ".mp4"
        if out == full:                       # исходник уже .mp4 (редкий hevc-in-mp4)
            out = os.path.splitext(full)[0] + "_web.mp4"
        print(f"  [{codec}] {os.path.relpath(full, ROOT)}  ->  {os.path.basename(out)}")
        cmd = [
            ff, "-y", "-loglevel", "error", "-i", full,
            "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "medium",
            "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart",
            out,
        ]
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if r.returncode != 0:
            print("    ! ошибка:", r.stderr.decode("utf-8", "ignore")[:200])

    print("\nготово. дальше:  py make_posters.py  и  py gen_data.py")


if __name__ == "__main__":
    main()
