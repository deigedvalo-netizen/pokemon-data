#!/usr/bin/env python3
"""
Job 1 Batch 5: Research cards 101-125 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
Rule: flag=1 ONLY with concrete evidence of specific re-release.
Default to flag=0 when in doubt.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_5_RESEARCH = [
    # Rows 102-126 of reprint_check.csv (cards 101-125)
    ("bw9-111", 0, "https://bulbapedia.bulbagarden.net/wiki/Deoxys-EX_(Plasma_Freeze_111)", "BW Plasma Freeze EX, no reprints"),
    ("neo4-9", 0, "https://bulbapedia.bulbagarden.net/wiki/Dark_Scizor_(Neo_Destiny_9)", "Neo Destiny exclusive"),
    ("neo4-111", 0, "https://bulbapedia.bulbagarden.net/wiki/Shining_Raichu_(Neo_Destiny_111)", "Shining Pokemon exclusive to Neo"),
    ("swshp-SWSH066", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_(SWSH_Black_Star_Promo_SWSH066)", "Sword/Shield era promo, unique"),
    ("sm3-150", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard-GX_(Burning_Shadows_150)", "SM-era Rainbow Rare, no reprints"),
    ("zsv10pt5-171", 0, "https://bulbapedia.bulbagarden.net/wiki/Victini_(Black_Bolt_171)", "Recent 2025 set, no reprints yet"),
    ("dpp-DP05", 0, "https://bulbapedia.bulbagarden.net/wiki/Tropical_Wind_(DP_Black_Star_Promo_DP05)", "Diamond/Pearl Black Star Promo, no reprints"),
    ("neo3-65", 0, "https://bulbapedia.bulbagarden.net/wiki/Shining_Gyarados_(Neo_Revelation_65)", "Shining Pokemon exclusive to Neo"),
    ("ex7-99", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Mewtwo_ex_(Team_Rocket_Returns_99)", "Team Rocket Returns EX, no reprints"),
    ("sv10-231", 0, "https://bulbapedia.bulbagarden.net/wiki/Team_Rocket%27s_Mewtwo_ex_(Destined_Rivals_231)", "Scarlet/Violet Special Illustration Rare 2025, no reprints yet"),
    ("ex14-4", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_%CE%B4_(Crystal_Guardians_4)", "Crystal Guardians delta Pokemon, no reprints"),
    ("ecard1-6", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_(Expedition_Base_Set_6)", "e-card era Expedition, no reprints"),
    ("sv8pt5-156", 0, "https://bulbapedia.bulbagarden.net/wiki/Sylveon_ex_(Prismatic_Evolutions_156)", "Scarlet/Violet 2025 Special Illustration Rare, no reprints yet"),
    ("zsv10pt5-172", 0, "https://bulbapedia.bulbagarden.net/wiki/Zekrom_ex_(Black_Bolt_172)", "Recent 2025 set, no reprints yet"),
    ("ru1-9", 0, "https://bulbapedia.bulbagarden.net/wiki/Mewtwo_(Pok%C3%A9mon_Rumble_9)", "Rumble set exclusive product"),
    ("base6-95", 1, "https://bulbapedia.bulbagarden.net/wiki/Squirtle_(Legendary_Collection_95)", "Legendary Collection Common reprint"),
    ("bw5-109", 0, "https://bulbapedia.bulbagarden.net/wiki/Gardevoir_(Dark_Explorers_109)", "BW Dark Explorers Secret Rare, no reprints"),
    ("col1-SL10", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_(Call_of_Legends_SL10)", "Call of Legends set, no reprints"),
    ("bw10-100", 0, "https://bulbapedia.bulbagarden.net/wiki/Palkia-EX_(Plasma_Blast_100)", "BW Plasma Blast EX, no reprints"),
    ("swsh12-186", 0, "https://bulbapedia.bulbagarden.net/wiki/Lugia_V_(Silver_Tempest_186)", "Sword/Shield Silver Tempest V, no reprints yet"),
    ("ex8-22", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_(Deoxys_22)", "EX Deoxys era rare, no reprints"),
    ("rsv10pt5-172", 0, "https://bulbapedia.bulbagarden.net/wiki/Victini_(White_Flare_172)", "Recent 2025 set, no reprints yet"),
    ("swsh7-192", 0, "https://bulbapedia.bulbagarden.net/wiki/Dragonite_V_(Evolving_Skies_192)", "Sword/Shield Evolving Skies V, no reprints"),
    ("xy4-121", 0, "https://bulbapedia.bulbagarden.net/wiki/M_Gengar-EX_(Phantom_Forces_121)", "XY Phantom Forces Secret Rare, no reprints"),
    ("np-27", 0, "https://bulbapedia.bulbagarden.net/wiki/Tropical_Tidal_Wave_(Nintendo_Black_Star_Promo_27)", "Nintendo Black Star Promo 2003, no reprints"),
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
    for card_id, flag, url, note in BATCH_5_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 5 (25 cards) complete.")
    print(f"Updated: {len(BATCH_5_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
