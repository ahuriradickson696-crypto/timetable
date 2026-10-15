"""Fix mojibake in frontend files. Keeps emojis."""
import os
import re

# Mojibake patterns to fix — using Unicode code points to avoid encoding issues
FIXES = [
    # En-dash and em-dash mojibake
    ("\u00c3\u00a2\u00e2\u201a\u00ac\u00e2\u20ac\u0153", "-"),  # en-dash
    ("\u00c3\u00a2\u00e2\u201a\u00ac\u00e2\u20ac\u009d", "-"),  # em-dash variant
    ("\u00c3\u00a2\u00e2\u201a\u00ac\u00e2\u20ac", "-"),        # em-dash
    ("\u00e2\u20ac\u201d", "-"),                                 # "
    ("\u00e2\u20ac\u201c", "-"),                                 # "
    ("\u00e2\u20ac\u00a6", "..."),                               # ellipsis

    # Arrows
    ("\u00c3\u00a2\u00e2\u201a\u00ac\u00e2\u20ac\u2122", "->"),
    ("\u00c3\u00a2\u00e2\u201a\u00ac\u00c5\u201c", "<-"),
    ("\u00e2\u2020\u2019", "->"),
    ("\u00e2\u2020\u2018", "<-"),

    # Quotes
    ("\u00c3\u00a2\u00e2\u201a\u00ac\u00e2\u201e\u00a2", "'"),
    ("\u00c3\u00a2\u00e2\u201a\u00ac\u00c5", "'"),
    ("\u00e2\u20ac\u2122", "'"),
    ("\u00e2\u20ac\u02dc", "'"),
    ("\u00e2\u20ac\u0153", '"'),
    ("\u00e2\u20ac\u009d", '"'),

    # Middle dot, bullet
    ("\u00c3\u201a\u00c2\u00b7", "-"),
    ("\u00c2\u00b7", "-"),
    ("\u00e2\u20ac\u00a2", "-"),

    # Standalone broken prefixes
    ("\u00c3\u201a", ""),
    ("\u00c3\u00a2", ""),
    ("\u00e2\u20ac", ""),
]

# Directories to process
ROOT = os.path.abspath(os.path.dirname(__file__))
# Frontend is sibling
FRONTEND = os.path.abspath(os.path.join(ROOT, "..", "..", "frontend"))

if not os.path.exists(FRONTEND):
    print("ERROR: frontend folder not found at", FRONTEND)
    exit(1)

print("Frontend:", FRONTEND)
print()

count = 0
for sub in ["src/pages", "src/components", "src/store", "src/api"]:
    full = os.path.join(FRONTEND, sub)
    if not os.path.exists(full):
        continue
    for dirpath, _, files in os.walk(full):
        for fn in files:
            if not (fn.endswith(".tsx") or fn.endswith(".ts")):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                print("  SKIP (encoding):", fn)
                continue

            original = content
            for bad, good in FIXES:
                content = content.replace(bad, good)

            if content != original:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(content)
                print("  Fixed:", fn)
                count += 1

print()
print("=" * 60)
print("Fixed " + str(count) + " files")
print("=" * 60)
