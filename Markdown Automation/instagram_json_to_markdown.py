#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description="Convertit un export JSON de messages Instagram en Markdown.")
    p.add_argument("input", type=Path, help="Fichier JSON d'entrée")
    p.add_argument("-o", "--output", type=Path, help="Fichier Markdown de sortie")
    args = p.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))

    blocks = []
    current_sender = None
    current_texts = []

    for msg in data.get("messages", []):
        sender = msg.get("sender", "Inconnu")
        text = msg.get("text") or ""
        text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            continue

        if sender == current_sender:
            current_texts.append(text)
        else:
            if current_texts:
                blocks.append(f"**{current_sender}**\n" + "\n\n".join(current_texts))
            current_sender = sender
            current_texts = [text]

    if current_texts:
        blocks.append(f"**{current_sender}**\n" + "\n\n".join(current_texts))

    output = args.output or args.input.with_suffix(".md")
    output.write_text("\n___\n\n".join(blocks) + "\n", encoding="utf-8")
    print(f"OK : {len(blocks)} blocs écrits dans {output}")

if __name__ == "__main__":
    main()