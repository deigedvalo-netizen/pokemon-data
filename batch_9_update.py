#!/usr/bin/env python3
"""
Job 1 Batch 9: Research cards 201-225 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
Rule: flag=1 ONLY with concrete evidence of specific re-release.
Default to flag=0 when in doubt.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_9_RESEARCH = [
    # Rows 202-226 of reprint_check.csv (cards 201-225)
    ("sv6-214", 0, "https://bulbapedia.bulbagarden.net/wiki/Greninja_ex_(Twilight_Masquerade_214)", "Scarlet/Violet 2024 SIR, no reprints yet"),
    ("ecard3-H24", 0, "https://bulbapedia.bulbagarden.net/wiki/Poliwrath_(Skyridge_H24)", "e-card Holo Rare, era exclusive"),
    ("sm11-242", 0, "https://bulbapedia.bulbagarden.net/wiki/Mewtwo_%26_Mew-GX_(Unified_Minds_242)", "SM Tag Team Rainbow, no reprints"),
    ("ex10-29", 0, "https://bulbapedia.bulbagarden.net/wiki/Lugia_(Unseen_Forces_29)", "EX Unseen Forces rare, no reprints"),
    ("base6-7", 1, "https://bulbapedia.bulbagarden.net/wiki/Dark_Raichu_(Legendary_Collection_7)", "Legendary Collection Rare Holo reprint"),
    ("ecard2-H11", 0, "https://bulbapedia.bulbagarden.net/wiki/Houndoom_(Aquapolis_H11)", "e-card Holo Rare, era exclusive"),
    ("neo2-1", 0, "https://bulbapedia.bulbagarden.net/wiki/Espeon_(Neo_Discovery_1)", "Neo Discovery exclusive"),
    ("ecard3-H13", 0, "https://bulbapedia.bulbagarden.net/wiki/Kabutops_(Skyridge_H13)", "e-card Holo Rare, era exclusive"),
    ("base6-74", 1, "https://bulbapedia.bulbagarden.net/wiki/Eevee_(Legendary_Collection_74)", "Legendary Collection Common reprint"),
    ("swsh7-189", 0, "https://bulbapedia.bulbagarden.net/wiki/Umbreon_V_(Evolving_Skies_189)", "Sword/Shield Evolving Skies V, no reprints"),
    ("xy6-105", 0, "https://bulbapedia.bulbagarden.net/wiki/M_Rayquaza-EX_(Roaring_Skies_105)", "XY Roaring Skies Rare Ultra, no reprints"),
    ("base6-38", 1, "https://bulbapedia.bulbagarden.net/wiki/Dark_Dragonair_(Legendary_Collection_38)", "Legendary Collection Uncommon reprint"),
    ("swsh7-212", 0, "https://bulbapedia.bulbagarden.net/wiki/Sylveon_VMAX_(Evolving_Skies_212)", "Sword/Shield Evolving Skies Rainbow VMAX, no reprints"),
    ("xyp-XY60", 0, "https://bulbapedia.bulbagarden.net/wiki/Gyarados_(XY_Black_Star_Promo_XY60)", "XY Black Star Promo, no reprints"),
    ("ex7-101", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Scizor_ex_(Team_Rocket_Returns_101)", "Team Rocket Returns EX, no reprints"),
    ("ex3-97", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_ex_(Dragon_Frontiers_97)", "Dragon Frontiers EX, no reprints"),
    ("ecard3-H22", 0, "https://bulbapedia.bulbagarden.net/wiki/Piloswine_(Skyridge_H22)", "e-card Holo Rare, era exclusive"),
    ("ex11-17", 0, "https://bulbapedia.bulbagarden.net/wiki/Umbreon_%CE%B4_(Delta_Species_17)", "Delta Species delta Pokemon, no reprints"),
    ("ex13-16", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_%CE%B4_(Holon_Phantoms_16)", "Holon Phantoms delta Pokemon, no reprints"),
    ("swshp-SWSH074", 0, "https://bulbapedia.bulbagarden.net/wiki/Special_Delivery_Pikachu_(SWSH_Black_Star_Promo_SWSH074)", "Sword/Shield Black Star Promo, no reprints"),
    ("ecard3-145", 0, "https://bulbapedia.bulbagarden.net/wiki/Celebi_(Skyridge_145)", "e-card Secret Rare, era exclusive"),
    ("sm9-186", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_%26_Mimikyu-GX_(Team_Up_186)", "SM Tag Team Rainbow, no reprints"),
    ("ex7-111", 0, "https://bulbapedia.bulbagarden.net/wiki/Here_Comes_Team_Rocket%21_(Team_Rocket_Returns_111)", "Team Rocket Returns Secret Rare, no reprints"),
    ("sm11-226", 0, "https://bulbapedia.bulbagarden.net/wiki/Mega_Sableye_%26_Tyranitar-GX_(Unified_Minds_226)", "SM Tag Team GX, no reprints"),
    ("swsh6-201", 0, "https://bulbapedia.bulbagarden.net/wiki/Blaziken_VMAX_(Chilling_Reign_201)", "Sword/Shield Chilling Reign Rainbow VMAX, no reprints"),
]

def update_db(card_id, reprint_flag):
    """Update reprint_flag in cards_metadata."""
    conn = sqlite3.connect('pokemon_prices.db')
    c = conn.cursor()
    c.execute('UPDATE cards_metadata SET reprint_flag=? WHERE card_id=?',
              (reprint_flag, card_id))
    conn.commit()
    conn.close()

def log_result(card_id, reprint_flag, url, note):
    """Log to progress file."""
    with open('hermes_reports/reprint_progress.csv', 'a') as f:
        f.write(f'{card_id},{reprint_flag},"{url}",{datetime.now().isoformat()},{note}\n')

if __name__ == '__main__':
    import os
    os.makedirs('hermes_reports', exist_ok=True)
    
    # Process each card
    for card_id, flag, url, note in BATCH_9_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 9 (25 cards) complete.")
    print(f"Updated: {len(BATCH_9_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
