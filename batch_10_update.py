#!/usr/bin/env python3
"""
Job 1 Batch 10: Research cards 226-250 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
Rule: flag=1 ONLY with concrete evidence of specific re-release.
Default to flag=0 when in doubt.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_10_RESEARCH = [
    # Rows 227-251 of reprint_check.csv (cards 226-250)
    ("np-7", 0, "https://bulbapedia.bulbagarden.net/wiki/Treecko_(Nintendo_Black_Star_Promo_7)", "Nintendo Black Star Promo 2003, no reprints"),
    ("xyp-XY124", 0, "https://bulbapedia.bulbagarden.net/wiki/Pikachu-EX_(XY_Black_Star_Promo_XY124)", "XY Black Star Promo, no reprints"),
    ("base2-11", 0, "https://bulbapedia.bulbagarden.net/wiki/Snorlax_(Jungle_11)", "Jungle Set rare, no reprints"),
    ("sv8-238", 0, "https://bulbapedia.bulbagarden.net/wiki/Pikachu_ex_(Surging_Sparks_238)", "Scarlet/Violet 2024 SIR, no reprints yet"),
    ("neo4-5", 0, "https://bulbapedia.bulbagarden.net/wiki/Dark_Feraligatr_(Neo_Destiny_5)", "Neo Destiny exclusive"),
    ("ru1-10", 0, "https://bulbapedia.bulbagarden.net/wiki/Mew_(Pok%C3%A9mon_Rumble_10)", "Rumble set exclusive product"),
    ("gym2-13", 0, "https://bulbapedia.bulbagarden.net/wiki/Misty%27s_Gyarados_(Gym_Challenge_13)", "Gym Challenge exclusive"),
    ("dpp-DP47", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_C_LV.X_(DP_Black_Star_Promo_DP47)", "Diamond/Pearl Black Star Promo, no reprints"),
    ("pl3-148", 0, "https://bulbapedia.bulbagarden.net/wiki/Articuno_(Supreme_Victors_148)", "Diamond/Pearl Supreme Victors Secret Rare, no reprints"),
    ("gym2-1", 0, "https://bulbapedia.bulbagarden.net/wiki/Blaine%27s_Arcanine_(Gym_Challenge_1)", "Gym Challenge exclusive"),
    ("ex10-117", 0, "https://bulbapedia.bulbagarden.net/wiki/Celebi_ex_(Unseen_Forces_117)", "EX Unseen Forces Secret Rare, no reprints"),
    ("np-36", 0, "https://bulbapedia.bulbagarden.net/wiki/Tropical_Tidal_Wave_(Nintendo_Black_Star_Promo_36)", "Nintendo Black Star Promo 2003, no reprints"),
    ("base6-4", 1, "https://bulbapedia.bulbagarden.net/wiki/Dark_Blastoise_(Legendary_Collection_4)", "Legendary Collection Rare Holo reprint"),
    ("base5-5", 0, "https://bulbapedia.bulbagarden.net/wiki/Dark_Dragonite_(Team_Rocket_5)", "Team Rocket exclusive"),
    ("bw11-115", 0, "https://bulbapedia.bulbagarden.net/wiki/Zekrom_(Legendary_Treasures_115)", "BW Legendary Treasures Secret Rare, no reprints"),
    ("ex7-102", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Scyther_ex_(Team_Rocket_Returns_102)", "Team Rocket Returns EX, no reprints"),
    ("me2-130", 0, "https://bulbapedia.bulbagarden.net/wiki/Mega_Charizard_X_ex_(Phantasmal_Flames_130)", "Recent 2025 set Mega Hyper Rare, no reprints yet"),
    ("base6-17", 1, "https://bulbapedia.bulbagarden.net/wiki/Ninetales_(Legendary_Collection_17)", "Legendary Collection Rare Holo reprint"),
    ("base6-37", 1, "https://bulbapedia.bulbagarden.net/wiki/Charmeleon_(Legendary_Collection_37)", "Legendary Collection Uncommon reprint"),
    ("ecard2-41", 0, "https://bulbapedia.bulbagarden.net/wiki/Umbreon_(Aquapolis_41)", "e-card rare, era exclusive"),
    ("ecard3-147", 0, "https://bulbapedia.bulbagarden.net/wiki/Crobat_(Skyridge_147)", "e-card Secret Rare, era exclusive"),
    ("neo3-3", 0, "https://bulbapedia.bulbagarden.net/wiki/Celebi_(Neo_Revelation_3)", "Neo Revelation exclusive"),
    ("ex13-5", 0, "https://bulbapedia.bulbagarden.net/wiki/Deoxys_%CE%B4_(Holon_Phantoms_5)", "Holon Phantoms delta Pokemon, no reprints"),
    ("ex13-8", 0, "https://bulbapedia.bulbagarden.net/wiki/Gyarados_%CE%B4_(Holon_Phantoms_8)", "Holon Phantoms delta Pokemon, no reprints"),
    ("gym1-13", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Scyther_(Gym_Heroes_13)", "Gym Heroes exclusive"),
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
    for card_id, flag, url, note in BATCH_10_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 10 (25 cards) complete.")
    print(f"Updated: {len(BATCH_10_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
