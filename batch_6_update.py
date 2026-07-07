#!/usr/bin/env python3
"""
Job 1 Batch 6: Research cards 126-150 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
Rule: flag=1 ONLY with concrete evidence of specific re-release.
Default to flag=0 when in doubt.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_6_RESEARCH = [
    # Rows 127-151 of reprint_check.csv (cards 126-150)
    ("ex3-90", 0, "https://bulbapedia.bulbagarden.net/wiki/Dragonite_ex_(Dragon_Frontiers_90)", "Dragon Frontiers EX, no reprints"),
    ("ex13-100", 0, "https://bulbapedia.bulbagarden.net/wiki/Mew_ex_(Holon_Phantoms_100)", "Holon Phantoms EX, no reprints"),
    ("bw7-146", 0, "https://bulbapedia.bulbagarden.net/wiki/White_Kyurem-EX_(Boundaries_Crossed_146)", "BW Boundaries Crossed EX, no reprints"),
    ("hgss3-86", 0, "https://bulbapedia.bulbagarden.net/wiki/Umbreon_(HS%E2%80%94Undaunted_86)", "HGSS Undaunted Rare Prime, no reprints"),
    ("swsh7-194", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_V_(Evolving_Skies_194)", "Sword/Shield Evolving Skies V, no reprints"),
    ("ex10-112", 0, "https://bulbapedia.bulbagarden.net/wiki/Umbreon_ex_(Unseen_Forces_112)", "EX Unseen Forces EX, no reprints"),
    ("neo4-14", 0, "https://bulbapedia.bulbagarden.net/wiki/Light_Dragonite_(Neo_Destiny_14)", "Neo Destiny exclusive"),
    ("ecard2-H28", 0, "https://bulbapedia.bulbagarden.net/wiki/Tyranitar_(Aquapolis_H28)", "e-card Holo Rare, era exclusive"),
    ("base6-68", 1, "https://bulbapedia.bulbagarden.net/wiki/Bulbasaur_(Legendary_Collection_68)", "Legendary Collection Common reprint"),
    ("ex12-92", 0, "https://bulbapedia.bulbagarden.net/wiki/Registeel_%E2%98%85_(Legend_Maker_92)", "Legend Maker Star Pokemon, no reprints"),
    ("dp5-98", 0, "https://bulbapedia.bulbagarden.net/wiki/Glaceon_LV.X_(Majestic_Dawn_98)", "Diamond/Pearl LV.X era, no reprints"),
    ("ex7-105", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Suicune_ex_(Team_Rocket_Returns_105)", "Team Rocket Returns EX, no reprints"),
    ("ex6-105", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_ex_(FireRed_%26_LeafGreen_105)", "FireRed & LeafGreen EX, no reprints"),
    ("ecard2-149", 0, "https://bulbapedia.bulbagarden.net/wiki/Lugia_(Aquapolis_149)", "e-card Secret Rare, era exclusive"),
    ("bp-8", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Mewtwo_(Best_of_Game_8)", "Best of Game promo 2002, no reprints"),
    ("ecard3-10", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_(Skyridge_10)", "e-card era rare, exclusive"),
    ("ex10-111", 0, "https://bulbapedia.bulbagarden.net/wiki/Tyranitar_ex_(Unseen_Forces_111)", "EX Unseen Forces EX, no reprints"),
    ("swshp-SWSH296", 0, "https://bulbapedia.bulbagarden.net/wiki/Champions_Festival_(SWSH_Black_Star_Promo_SWSH296)", "Sword/Shield Black Star Promo, no reprints"),
    ("ecard1-4", 0, "https://bulbapedia.bulbagarden.net/wiki/Blastoise_(Expedition_Base_Set_4)", "e-card Expedition Rare Holo, exclusive"),
    ("neo2-13", 0, "https://bulbapedia.bulbagarden.net/wiki/Umbreon_(Neo_Discovery_13)", "Neo Discovery exclusive"),
    ("bw9-120", 0, "https://bulbapedia.bulbagarden.net/wiki/Garchomp_(Plasma_Freeze_120)", "BW Plasma Freeze Secret Rare, no reprints"),
    ("ex7-100", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Moltres_ex_(Team_Rocket_Returns_100)", "Team Rocket Returns EX, no reprints"),
    ("hgss4-94", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_(HS%E2%80%94Triumphant_94)", "HGSS Triumphant Rare Prime, no reprints"),
    ("dc1-6", 0, "https://bulbapedia.bulbagarden.net/wiki/Team_Aqua%27s_Kyogre-EX_(Double_Crisis_6)", "Double Crisis EX, no reprints"),
    ("base6-88", 1, "https://bulbapedia.bulbagarden.net/wiki/Psyduck_(Legendary_Collection_88)", "Legendary Collection Common reprint"),
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
    for card_id, flag, url, note in BATCH_6_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 6 (25 cards) complete.")
    print(f"Updated: {len(BATCH_6_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
