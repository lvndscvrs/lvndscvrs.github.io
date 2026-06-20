# -*- coding: utf-8 -*-
import os, json, re, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))


def poster_for(rel):
    """Возвращает относительный путь к постеру, если он сгенерирован make_posters.py."""
    safe = hashlib.md5(rel.encode("utf-8")).hexdigest() + ".jpg"
    if os.path.exists(os.path.join(ROOT, "posters", safe)):
        return "posters/" + safe
    return None

# folder -> (rubric key, rubric label, group)
FOLDER_MAP = {
    os.path.join("Реклама", "HYPER"):              ("hyper",   "HYPER",            "Реклама"),
    os.path.join("Реклама", "HYPER фулл ИИ"):       ("hyper-ai","HYPER · ИИ",       "Реклама"),
    os.path.join("Реклама", "Видео для соцсетей"):  ("social",  "Соцсети",          "Реклама"),
    os.path.join("Реклама", "Креативы имиджевые"):  ("image",   "Имиджевые",        "Реклама"),
    os.path.join("Реклама", "Креативы типовые"):    ("typical", "Типовые",          "Реклама"),
    os.path.join("Спортивные Меропртия"):            ("sport",   "Спорт",            "Спортивные мероприятия"),
}

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VID_EXT = {".mp4", ".mov", ".webm", ".m4v"}

def nice_title(name):
    base = os.path.splitext(name)[0]
    base = re.sub(r"[_]+", " ", base)
    base = re.sub(r"\s+", " ", base).strip()
    return base

items = []
for folder, (rkey, rlabel, group) in FOLDER_MAP.items():
    abs_dir = os.path.join(ROOT, folder)
    if not os.path.isdir(abs_dir):
        continue
    for fn in sorted(os.listdir(abs_dir)):
        ext = os.path.splitext(fn)[1].lower()
        if ext in IMG_EXT:
            mtype = "image"
        elif ext in VID_EXT:
            mtype = "video"
            # если рядом есть веб-версия .mp4 с тем же именем — исходник пропускаем
            stem = os.path.splitext(fn)[0]
            if ext != ".mp4" and os.path.exists(os.path.join(abs_dir, stem + ".mp4")):
                continue
        else:
            continue
        rel = folder.replace("\\", "/") + "/" + fn
        size = os.path.getsize(os.path.join(abs_dir, fn))
        entry = {
            "src": rel,
            "type": mtype,
            "rubric": rkey,
            "rubricLabel": rlabel,
            "group": group,
            "title": nice_title(fn),
            "size": size,
            "ext": ext.lstrip("."),
        }
        if mtype == "video":
            poster = poster_for(rel)
            if poster:
                entry["poster"] = poster
        items.append(entry)

rubrics = []
seen = set()
for folder, (rkey, rlabel, group) in FOLDER_MAP.items():
    if rkey not in seen:
        seen.add(rkey)
        rubrics.append({"key": rkey, "label": rlabel, "group": group})

data = {"rubrics": rubrics, "items": items}

out = "window.PORTFOLIO = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
with open(os.path.join(ROOT, "data.js"), "w", encoding="utf-8") as f:
    f.write(out)

print("items:", len(items))
for r in rubrics:
    c = sum(1 for i in items if i["rubric"] == r["key"])
    print(f"  {r['label']}: {c}")
