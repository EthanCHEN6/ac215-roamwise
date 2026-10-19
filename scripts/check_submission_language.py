"""Check submitted text, filenames and Office XML for Han characters.

Run in the test container. The input list is produced by git ls-files on the host.
Raster images require a separate visual check.
"""
import json
from pathlib import Path
import re
import sys
import zipfile

HAN = re.compile("[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]")
root, file_list = map(Path, sys.argv[1:3])
issues, checked, images = [], 0, []
for name in file_list.read_text(encoding="utf-8-sig").splitlines():
    path = root / name
    if not path.is_file():
        continue
    if HAN.search(name):
        issues.append({"file": name, "location": "filename"})
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        images.append(name)
        continue
    if path.suffix.lower() in {".pptx", ".docx", ".xlsx", ".zip"}:
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if HAN.search(member):
                    issues.append({"file": name, "location": member})
                if member.endswith((".xml", ".md", ".html", ".json", ".txt")):
                    text = archive.read(member).decode("utf-8", errors="replace")
                    if HAN.search(text):
                        issues.append({"file": name, "location": member})
        checked += 1
        continue
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeError:
        issues.append({"file": name, "location": "uninspected binary"})
        continue
    if path.suffix == ".json":
        text = json.dumps(json.loads(text), ensure_ascii=False)
    if HAN.search(text):
        issues.append({"file": name, "location": "content"})
    checked += 1
print(json.dumps({"checked_files": checked, "issues": issues, "images_for_visual_review": images}, indent=2, ensure_ascii=False))
sys.exit(bool(issues))
