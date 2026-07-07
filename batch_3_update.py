#!/usr/bin/env python3
"""
Job 1 Batch 3: Research cards 51-75 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
Rule: flag=1 ONLY with concrete evidence of specific re-release.
Default to flag=0 when in doubt.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_3_RESEARCH = [
    # Rows 52-76 of reprint_check.csv (cards 51-75)
    ("ecard3-150", 0, "https://bulbapedia.bulbagarden.net/wiki/Kabutops_(Skyridge_150)", "e-card Secret Rare, era exclusive"),
    ("bwp-BW50", 0, "https://bulbapedia.bulbagarden.net/wiki/Tropical_Beach_(BW_Black_Star_Promo_50)", "BW Black Star Promo variant, unique"),
    ("hgss1-115", 0, "https://bulbapedia.bulbagarden.net/wiki/Grass_Energy_(HeartGold_%26_SoulSilver_115)", "Common Energy, no special reprints"),
    ("xy4-122", 0, "https://bulbapedia.bulbagarden.net/wiki/Dialga-EX_(Phantom_Forces_122)", "Secret rare XY-era, no reprints"),
    ("xy7-98", 0, "https://bulbapedia.bulbagarden.net/wiki/M_Rayquaza-EX_(Ancient_Origins_98)", "Secret rare XY-era, no reprints"),
    ("neo4-110", 0, "https://bulbapedia.bulbagarden.net/wiki/Shining_Noctowl_(Neo_Destiny_110)", "Shining Pokémon exclusive to Neo"),
    ("ex11-113", 0, "https://bulbapedia.bulbagarden.net/wiki/Metagross_★_(Delta_Species_113)", "Delta Pokémon exclusive"),
    ("ex14-100", 0, "https://bulbapedia.bulbagarden.net/wiki/Celebi_★_(Crystal_Guardians_100)", "Star Pokémon exclusive"),
    ("neo4-109", 0, "https://bulbapedia.bulbagarden.net/wiki/Shining_Mewtwo_(Neo_Destiny_109)", "Shining Pokémon exclusive to Neo"),
    ("ex10-105", 0, "https://bulbapedia.bulbagarden.net/wiki/Lugia_ex_(Unseen_Forces_105)", "EX-era card, no reprints"),
    ("ex16-102", 0, "https://bulbapedia.bulbagarden.net/wiki/Vaporeon_★_(Power_Keepers_102)", "Star Pokémon exclusive"),
    ("ex7-97", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Entei_ex_(Team_Rocket_Returns_97)", "Team Rocket Returns EX, no reprints"),
    ("ex7-104", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Snorlax_ex_(Team_Rocket_Returns_104)", "Team Rocket Returns EX, no reprints"),
    ("ex7-106", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Zapdos_ex_(Team_Rocket_Returns_106)", "Team Rocket Returns EX, no reprints"),
    ("gym2-2", 0, "https://bulbapedia.bulbagarden.net/wiki/Blaine%27s_Charizard_(Gym_Challenge_2)", "Gym Challenge era, no reprints"),
    ("swsh11-186", 0, "https://bulbapedia.bulbagarden.net/wiki/Giratina_V_(Lost_Origin_186)", "Lost Origin done printing"),
    ("sm9-161", 0, "https://bulbapedia.bulbagarden.net/wiki/Magikarp_%26_Wailord-GX_(Team_Up_161)", "GX-era Tag Team, no reprints"),
    ("svp-45", 0, "https://bulbapedia.bulbagarden.net/wiki/Paradise_Resort_(Scarlet_%26_Violet_Black_Star_Promo_45)", "SV-era promo, unique"),
    ("me2-125", 0, "https://bulbapedia.bulbagarden.net/wiki/Mega_Charizard_X_ex_(Phantasmal_Flames_125)", "Recent special set 2025, no reprints yet"),
    ("ecard3-149", 0, "https://bulbapedia.bulbagarden.net/wiki/Ho-oh_(Skyridge_149)", "e-card Secret Rare, era exclusive"),
    ("base6-18", 0, "https://bulbapedia.bulbagarden.net/wiki/Venusaur_(Legendary_Collection_18)", "Legendary Collection is reprint set, no further reprints"),
    ("base6-86", 0, "https://bulbapedia.bulbagarden.net/wiki/Pikachu_(Legendary_Collection_86)", "Legendary Collection Common, no reprints"),
    ("ecard1-13", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_(Expedition_Base_Set_13)", "e-card era, exclusive"),
    ("ecard1-9", 0, "https://bulbapedia.bulbagarden.net/wiki/Dragonite_(Expedition_Base_Set_9)", "e-card era, exclusive"),
    ("pl2-111", 0, "https://bulbapedia.bulbagarden.net/wiki/Snorlax_LV.X_(Rising_Rivals_111)", "LV.X era, no reprints"),
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
    for card_id, flag, url, note in BATCH_3_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 3 (25 cards) complete.")
    print(f"Updated: {len(BATCH_3_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
