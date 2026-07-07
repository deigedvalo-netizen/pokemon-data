#!/usr/bin/env python3
"""
Job 1 Batch 12: Research cards 276-300 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
Rule: flag=1 ONLY with concrete evidence of specific re-release.
Default to flag=0 when in doubt.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_12_RESEARCH = [
    # Rows 277-301 of reprint_check.csv (cards 276-300)
    ("col1-SL11", 0, "https://bulbapedia.bulbagarden.net/wiki/Suicune_(Call_of_Legends_SL11)", "Call of Legends set, no reprints"),
    ("sv8pt5-155", 0, "https://bulbapedia.bulbagarden.net/wiki/Espeon_ex_(Prismatic_Evolutions_155)", "Scarlet/Violet 2025 SIR, no reprints yet"),
    ("gym2-14", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Mewtwo_(Gym_Challenge_14)", "Gym Challenge exclusive"),
    ("pl2-112", 0, "https://bulbapedia.bulbagarden.net/wiki/Pikachu_(Rising_Rivals_112)", "Diamond/Pearl Rising Rivals Secret Rare, no reprints"),
    ("basep-24", 0, "https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Trainer_Pikachu_(Wizards_Black_Star_Promo_24)", "Wizards Black Star Promo 1999, no reprints"),
    ("ex11-40", 0, "https://bulbapedia.bulbagarden.net/wiki/Ditto_(Delta_Species_40)", "Delta Species Uncommon, no reprints"),
    ("bw5-103", 0, "https://bulbapedia.bulbagarden.net/wiki/Entei-EX_(Dark_Explorers_103)", "BW Dark Explorers EX, no reprints"),
    ("bw11-114", 0, "https://bulbapedia.bulbagarden.net/wiki/Reshiram_(Legendary_Treasures_114)", "BW Legendary Treasures Secret Rare, no reprints"),
    ("neo1-12", 0, "https://bulbapedia.bulbagarden.net/wiki/Pichu_(Neo_Genesis_12)", "Neo Genesis exclusive"),
    ("bw5-104", 0, "https://bulbapedia.bulbagarden.net/wiki/Kyogre-EX_(Dark_Explorers_104)", "BW Dark Explorers EX, no reprints"),
    ("bw5-105", 0, "https://bulbapedia.bulbagarden.net/wiki/Raikou-EX_(Dark_Explorers_105)", "BW Dark Explorers EX, no reprints"),
    ("sm9-164", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_%26_Mimikyu-GX_(Team_Up_164)", "SM Team Up Rare Ultra, no reprints"),
    ("ex11-12", 0, "https://bulbapedia.bulbagarden.net/wiki/Mewtwo_%CE%B4_(Delta_Species_12)", "Delta Species delta Pokemon, no reprints"),
    ("smp-SM191", 0, "https://bulbapedia.bulbagarden.net/wiki/Mewtwo_%26_Mew-GX_(SM_Black_Star_Promo_SM191)", "SM Black Star Promo, no reprints"),
    ("ex4-94", 0, "https://bulbapedia.bulbagarden.net/wiki/Suicune_ex_(Team_Magma_vs_Team_Aqua_94)", "EX Team Magma vs Team Aqua EX, no reprints"),
    ("sm10-201", 0, "https://bulbapedia.bulbagarden.net/wiki/Greninja_%26_Zoroark-GX_(Unbroken_Bonds_201)", "SM Tag Team GX, no reprints"),
    ("ecard2-H19", 0, "https://bulbapedia.bulbagarden.net/wiki/Ninetales_(Aquapolis_H19)", "e-card Holo Rare, era exclusive"),
    ("bwp-BW85", 0, "https://bulbapedia.bulbagarden.net/wiki/Lucario_(BW_Black_Star_Promo_BW85)", "BW Black Star Promo, no reprints"),
    ("ecard3-H2", 0, "https://bulbapedia.bulbagarden.net/wiki/Arcanine_(Skyridge_H2)", "e-card Holo Rare, era exclusive"),
    ("ex1-101", 0, "https://bulbapedia.bulbagarden.net/wiki/Mewtwo_ex_(Ruby_%26_Sapphire_101)", "EX Ruby & Sapphire EX, no reprints"),
    ("ecard3-H4", 0, "https://bulbapedia.bulbagarden.net/wiki/Beedrill_(Skyridge_H4)", "e-card Holo Rare, era exclusive"),
    ("pl2-114", 0, "https://bulbapedia.bulbagarden.net/wiki/Surfing_Pikachu_(Rising_Rivals_114)", "Diamond/Pearl Rising Rivals Secret Rare, no reprints"),
    ("sv8pt5-149", 0, "https://bulbapedia.bulbagarden.net/wiki/Vaporeon_ex_(Prismatic_Evolutions_149)", "Scarlet/Violet 2025 SIR, no reprints yet"),
    ("ru1-3", 0, "https://bulbapedia.bulbagarden.net/wiki/Ninetales_(Pok%C3%A9mon_Rumble_3)", "Rumble set exclusive product"),
    ("xyp-XY150a", 0, "https://bulbapedia.bulbagarden.net/wiki/Yveltal-EX_(XY_Black_Star_Promo_XY150a)", "XY Black Star Promo, no reprints"),
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
    for card_id, flag, url, note in BATCH_12_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 12 (25 cards) complete.")
    print(f"Updated: {len(BATCH_12_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
