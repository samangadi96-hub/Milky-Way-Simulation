"""One-shot fixer: replaces the unicode HUD block in main.py with plain ASCII."""
import re, pathlib

path = pathlib.Path(__file__).parent / "main.py"
src = path.read_text(encoding="utf-8")

# Match the print-block that starts right after the move_right assignment
# and ends just before BASE_DIR = ...
pattern = re.compile(
    r"(        self\.move_right = False\r?\n)"   # anchor line before block
    r"\r?\n"
    r"        print\(\)\r?\n"
    r"(?:        print\([^\n]+\)\r?\n)+"         # all the unicode print lines
    r"        print\(\)\r?\n"
    r"(\r?\n)"                                   # blank line after block
)

replacement = (
    r"\g<1>"
    "\n"
    "        print()\n"
    "        print('  Milky Way Simulation - Controls')\n"
    "        print('  --------------------------------')\n"
    "        print('  Mouse Left-drag  -> orbit galaxy')\n"
    "        print('  Mouse Scroll     -> zoom in / out')\n"
    "        print('  W/S / Up/Down    -> tilt camera')\n"
    "        print('  A/D / Left/Right -> rotate camera')\n"
    "        print('  Q / E            -> zoom in / out')\n"
    "        print('  --------------------------------')\n"
    "        print()\n"
    r"\g<2>"
)

new_src, count = pattern.subn(replacement, src)
if count == 0:
    # Fallback: just wipe every print line that contains box-drawing chars
    lines = src.splitlines(keepends=True)
    BOX_CHARS = "\u250c\u2500\u2502\u2514\u2192\u2328\ud83d\uddb1\u2191\u2193\u2190\u2192"
    new_lines = []
    skip_next_empty = False
    for line in lines:
        if any(c in line for c in BOX_CHARS):
            continue  # drop bad line
        new_lines.append(line)
    new_src = "".join(new_lines)
    print(f"Fallback used: removed lines with box-drawing chars.")
else:
    print(f"Replaced HUD block ({count} match(es)).")

path.write_text(new_src, encoding="utf-8")
print("Done. main.py updated.")
