"""Set a PPTX's creator and lastModifiedBy (docProps/core.xml) to the user's name. Other zip parts stay byte-identical.

    python ppt_meta.py [--name "Your Name"] <deck.pptx> [...]

The name comes from --name, else from config.local.json ({"author": "..."}) next to SKILL.md
(created on first run; never committed). Title, company etc. are left alone.
"""
import json
import os
import sys
import zipfile

from lxml import etree

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.local.json")
NAME = None
NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
}


def set_meta(path: str) -> None:
    tmp = path + ".meta.tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w") as zout:
        if "docProps/core.xml" not in zin.namelist():
            raise RuntimeError(f"docProps/core.xml 없음: {path}")
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "docProps/core.xml":
                root = etree.fromstring(data)
                for pre, local in (("dc", "creator"), ("cp", "lastModifiedBy")):
                    tag = f"{{{NS[pre]}}}{local}"
                    el = root.find(tag)
                    if el is None:
                        el = etree.SubElement(root, tag)
                    el.text = NAME
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            zout.writestr(info, data)
    os.replace(tmp, path)


def show(path: str) -> None:
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read("docProps/core.xml"))
    vals = {k: (root.findtext(f"{{{NS[p]}}}{k}") or "") for p, k in (("dc", "creator"), ("cp", "lastModifiedBy"))}
    print(f"{os.path.basename(path)}: creator={vals['creator']!r} lastModifiedBy={vals['lastModifiedBy']!r}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--name" in args:
        i = args.index("--name"); NAME = args[i + 1]; del args[i:i + 2]
    elif os.path.exists(CONFIG):
        NAME = json.load(open(CONFIG, encoding="utf-8")).get("author")
    if not args or not NAME:
        sys.exit(__doc__ + "\n(no author name: pass --name or create config.local.json)")
    for p in args:
        set_meta(p)
        show(p)
