# -*- coding: utf-8 -*-
"""
Генерирует постеры (превью-кадры) для всех видео и кладёт их в папку posters/.
Запуск:  py make_posters.py
Нужен ffmpeg (ищется в PATH или по известному пути установки winget).
После прогона перезапусти gen_data.py не нужно — make_posters сам ничего не пишет в data.js,
поставщик постеров встроен в gen_data.py (ищет posters/<тот же путь>.jpg).
"""
import os
import sys
import shutil
import hashlib
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTERS = os.path.join(ROOT, "posters")

VID_EXT = {".mp4", ".mov", ".webm", ".m4v"}
SKIP_DIRS = {"posters", "deploy", "__pycache__"}

# момент кадра: берём ~1 сек (часто на 0с чёрный кадр)
SEEK = "00:00:01"


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages")
    for dirpath, _, files in os.walk(base):
        if "ffmpeg.exe" in files:
            return os.path.join(dirpath, "ffmpeg.exe")
    return None


def poster_path(rel):
    """posters/<хэш-папки>/<имя>.jpg — плоско и без проблем с кириллицей."""
    safe = hashlib.md5(rel.encode("utf-8")).hexdigest() + ".jpg"
    return os.path.join(POSTERS, safe)


def iter_videos():
    for dirpath, dirnames, files in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in files:
            if os.path.splitext(fn)[1].lower() in VID_EXT:
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ROOT).replace("\\", "/")
                yield rel, full


def main():
    ff = find_ffmpeg()
    if not ff:
        print("ffmpeg не найден. Установи: winget install Gyan.FFmpeg")
        sys.exit(1)
    print("ffmpeg:", ff)

    os.makedirs(POSTERS, exist_ok=True)
    ok = skip = fail = 0

    for rel, full in iter_videos():
        out = poster_path(rel)
        if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(full):
            skip += 1
            continue
        cmd = [
            ff, "-y", "-loglevel", "error",
            "-ss", SEEK, "-i", full,
            "-frames:v", "1",
            "-vf", "scale=640:-2",
            "-q:v", "4",
            out,
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if res.returncode != 0 or not os.path.exists(out):
            # запасной вариант: кадр на 0с (для очень коротких роликов)
            cmd2 = [ff, "-y", "-loglevel", "error", "-i", full,
                    "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "4", out]
            res = subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if os.path.exists(out):
            ok += 1
            print("  +", rel)
        else:
            fail += 1
            print("  ! не удалось:", rel, res.stderr.decode("utf-8", "ignore")[:120])

    print(f"\nготово: создано {ok}, пропущено {skip}, ошибок {fail}")
    print("теперь запусти:  py gen_data.py")


if __name__ == "__main__":
    main()
