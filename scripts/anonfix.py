#!/usr/bin/env python3
import argparse
from pathlib import Path

RED = "\033[91m"
RESET = "\033[0m"


def main():
    parser = argparse.ArgumentParser(
        description="Preview and optionally replace instances of a string one at a time."
    )
    parser.add_argument("file", help="File to edit, e.g. ./game_notebook.ipynb")
    parser.add_argument("word", help="Word/string to replace")
    parser.add_argument(
        "-r", "--replacement",
        default="ANON",
        help="Replacement string. Default: ANON",
    )

    args = parser.parse_args()

    path = Path(args.file)
    word = args.word
    replacement = args.replacement

    text = path.read_text(encoding="utf-8")
    total = text.count(word)

    if total == 0:
        print(f"No instances of {word!r} found in {path}")
        return

    print(f"Found {total} instance(s) of {word!r} in {path}\n")

    result = []
    i = 0
    seen = 0
    replaced = 0
    replace_all = False

    while True:
        idx = text.find(word, i)
        if idx == -1:
            result.append(text[i:])
            break

        seen += 1

        result.append(text[i:idx])

        if replace_all:
            result.append(replacement)
            replaced += 1
            i = idx + len(word)
            continue

        before = text[max(0, idx - 120):idx]
        after = text[idx + len(word):idx + len(word) + 120]

        print("=" * 80)
        print(f"Instance {seen}/{total}")
        print(before + f"{RED}{word}{RESET}" + after)

        answer = input("Replace this instance? [y/N/a/q] ").strip().lower()

        if answer == "y":
            result.append(replacement)
            replaced += 1
        elif answer == "a":
            result.append(replacement)
            replaced += 1
            replace_all = True
        else:
            result.append(word)

        i = idx + len(word)

        if answer == "q":
            result.append(text[i:])
            break

    if replaced > 0:
        path.write_text("".join(result), encoding="utf-8")
        print(f"\nReplaced {replaced}/{total} instance(s) in {path}")
    else:
        print("\nNo changes made.")


if __name__ == "__main__":
    main()