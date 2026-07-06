#!/usr/bin/env python3
"""
Reusable card-name -> species normalizer.

Maps TCG card names to a base species so "Pikachu VMAX", "Pikachu ex",
"Detective Pikachu" and "Pikachu V-UNION" all group as species = "Pikachu".

Import and reuse anywhere:

    from species_normalizer import normalize_species
    normalize_species("Reshiram & Charizard-GX", "Pokémon")  # "Reshiram & Charizard"
    normalize_species("Ultra Ball", "Trainer")               # None

Rules (applied in order; only for supertype == 'Pokémon', else None):
  1. Exact-match override dict (SPECIES_OVERRIDES) — wins over everything.
  2. Strip owner prefix:      "Team Rocket's Meowth" -> "Meowth"
  3. Strip style prefixes:    Dark / Light / Shining / Radiant / Mega / M
  4. Strip mechanic suffixes: ex EX V VMAX VSTAR V-UNION GX BREAK LV.X
                              LEGEND Prime δ ★ ◇ Star G GL E4 FB C
                              (and hyphenated -EX / -GX, e.g. "Charizard-EX")
  5. Collapse form variants:  "Deoxys Attack Forme" -> "Deoxys",
                              "Burmy Sandy Cloak"   -> "Burmy"
  6. Tag Teams keep the pair: "Pikachu & Zekrom-GX" -> "Pikachu & Zekrom"
     (a Tag Team's price behaves like its own product, not like either
      member; change KEEP_TAG_TEAM_PAIRS to False to take the first name)

Deliberate defaults (edit the flags to change):
  - Regional forms are KEPT ("Alolan Vulpix" != "Vulpix"): collectors and
    the market treat them as distinct. STRIP_REGIONAL_FORMS = True to merge.
  - "Iron Hands", "Tapu Koko", "Mr. Mime", "Porygon-Z", "Type: Null" etc.
    are real species names and are never touched (suffix stripping works on
    whole trailing tokens only, so internal hyphens/words are safe).
"""

import re

STRIP_REGIONAL_FORMS = False   # True: "Alolan Vulpix" -> "Vulpix"
KEEP_TAG_TEAM_PAIRS = True     # False: "Pikachu & Zekrom" -> "Pikachu"

# Exact full-name overrides. Checked first. Extend freely.
SPECIES_OVERRIDES = {
    "Detective Pikachu": "Pikachu",
    "Surfing Pikachu": "Pikachu",
    "Flying Pikachu": "Pikachu",
    "Birthday Pikachu": "Pikachu",
    "Armored Mewtwo": "Mewtwo",
    "Pikachu with Grey Felt Hat": "Pikachu",
}

# Whole trailing tokens stripped repeatedly (order-independent).
_SUFFIX_TOKENS = {
    "ex", "EX", "V", "VMAX", "VSTAR", "V-UNION", "GX", "BREAK",
    "LV.X", "LEGEND", "Prime", "δ", "★", "◇", "Star",
    "G", "GL", "E4", "FB", "C",   # SP-engine tags (Platinum era)
}

_STYLE_PREFIXES = ("Dark ", "Light ", "Shining ", "Radiant ", "Mega ", "M ")
_REGIONAL_PREFIXES = ("Alolan ", "Galarian ", "Hisuian ", "Paldean ")

_OWNER_RE = re.compile(r"^[\w\.\?_ ]{1,20}'s\s+")          # Lt. Surge's, _____'s, Imakuni?'s
_HYPHEN_MECH_RE = re.compile(r"-(EX|GX)$")                  # Charizard-EX, ...& Zekrom-GX
_FORM_RE = re.compile(r"\s+\S+\s+(Forme?|Cloak)$")          # "<sp> Attack Forme", "<sp> Sandy Cloak"


def _strip_one_name(name: str) -> str:
    name = _OWNER_RE.sub("", name).strip()
    changed = True
    while changed:
        changed = False
        for p in _STYLE_PREFIXES:
            if name.startswith(p) and len(name) > len(p):
                name = name[len(p):]
                changed = True
        if STRIP_REGIONAL_FORMS:
            for p in _REGIONAL_PREFIXES:
                if name.startswith(p) and len(name) > len(p):
                    name = name[len(p):]
                    changed = True
        new = _HYPHEN_MECH_RE.sub("", name)
        if new != name:
            name, changed = new, True
        parts = name.split(" ")
        if len(parts) > 1 and parts[-1] in _SUFFIX_TOKENS:
            name, changed = " ".join(parts[:-1]), True
    name = _FORM_RE.sub("", name)
    return name.strip()


def normalize_species(card_name: str, supertype: str | None) -> str | None:
    """Return normalized species for a Pokémon card, None for Trainer/Energy."""
    if supertype != "Pokémon" or not card_name:
        return None
    if card_name in SPECIES_OVERRIDES:
        return SPECIES_OVERRIDES[card_name]
    # Tag Team / multi-Pokémon cards ("A & B-GX", "A & B & C-GX")
    if " & " in card_name:
        members = [_strip_one_name(m) for m in card_name.split(" & ")]
        return " & ".join(members) if KEEP_TAG_TEAM_PAIRS else members[0]
    return _strip_one_name(card_name)


if __name__ == "__main__":
    # Audit mode: print distinct name -> species mapping from the local DB.
    import csv
    import sqlite3
    import sys

    db = sys.argv[1] if len(sys.argv) > 1 else "pokemon_prices.db"
    out = sys.argv[2] if len(sys.argv) > 2 else "species_map.csv"
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT DISTINCT name, supertype FROM cards WHERE supertype='Pokémon' ORDER BY name"
    ).fetchall()
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["card_name", "species"])
        for name, st in rows:
            w.writerow([name, normalize_species(name, st)])
    print(f"Wrote {len(rows)} name->species pairs to {out} — review the unusual ones "
          f"and add corrections to SPECIES_OVERRIDES.")
