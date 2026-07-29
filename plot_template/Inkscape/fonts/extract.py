import re
import sys
from pathlib import Path

from fontTools.ttLib import TTCollection


def get_font_name(font):
    """Get a suitable filename from the font's name table."""
    name_table = font["name"]

    # Prefer PostScript name, then full font name.
    for name_id in (6, 4, 1):
        for record in name_table.names:
            if record.nameID == name_id:
                try:
                    name = record.toUnicode().strip()
                except UnicodeDecodeError:
                    continue

                if name:
                    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)

    return None


if len(sys.argv) != 2:
    print("Usage: python3 split_ttc.py FONT_FILE.ttc")
    raise SystemExit(1)

input_path = Path(sys.argv[1]).expanduser().resolve()
output_directory = input_path.parent / f"{input_path.stem}_extracted"
output_directory.mkdir(exist_ok=True)

collection = TTCollection(str(input_path), lazy=False)

for index, font in enumerate(collection.fonts):
    font_name = get_font_name(font) or f"font_{index}"

    extension = ".otf" if "CFF " in font or "CFF2" in font else ".ttf"
    output_path = output_directory / f"{font_name}{extension}"

    # A copied signature becomes invalid when the font is rewritten.
    if "DSIG" in font:
        del font["DSIG"]

    font.recalcBBoxes = True
    font.recalcTimestamp = True
    font.flavor = None

    font.save(str(output_path), reorderTables=True)
    print(f"Extracted: {output_path}")

collection.close()

