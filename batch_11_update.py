#!/usr/bin/env python3
"""
Job 1 Batch 11: Research cards 251-275 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
Rule: flag=1 ONLY with concrete evidence of specific re-release.
Default to flag=0 when in doubt.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_11_RESEARCH = [
    # Rows 252-276 of reprint_check.csv (cards 251-275)
    ("bwp-BW97", 0, "https://bulbapedia.bulbagarden.net/wiki/Eevee_(BW_Black_Star_Promo_BW97)", "BW Black Star Promo, no reprints"),
    ("ecard3-75", 0, "https://bulbapedia.bulbagarden.net/wiki/Magikarp_(Skyridge_75)", "e-card Common, era exclusive"),
    ("neo3-13", 0, "https://bulbapedia.bulbagarden.net/wiki/Raikou_(Neo_Revelation_13)", "Neo Revelation exclusive"),
    ("swsh8-270", 0, "https://bulbapedia.bulbagarden.net/wiki/Espeon_VMAX_(Fusion_Strike_270)", "Sword/Shield Fusion Strike Rainbow VMAX, no reprints"),
    ("xy6-77a", 0, "https://bulbapedia.bulbagarden.net/wiki/Shaymin-EX_(Roaring_Skies_77a)", "XY Roaring Skies Rare Ultra, no reprints"),
    ("swsh9-154", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_V_(Brilliant_Stars_154)", "Sword/Shield Brilliant Stars V, no reprints"),
    ("sm11-235", 0, "https://bulbapedia.bulbagarden.net/wiki/Misty%27s_Favor_(Unified_Minds_235)", "SM Unified Minds Rare Ultra, no reprints"),
    ("ex7-103", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Sneasel_ex_(Team_Rocket_Returns_103)", "Team Rocket Returns EX, no reprints"),
    ("ecard3-H20", 0, "https://bulbapedia.bulbagarden.net/wiki/Moltres_(Skyridge_H20)", "e-card Holo Rare, era exclusive"),
    ("base6-9", 1, "https://bulbapedia.bulbagarden.net/wiki/Dark_Vaporeon_(Legendary_Collection_9)", "Legendary Collection Rare Holo reprint"),
    ("sv4pt5-234", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_ex_(Paldean_Fates_234)", "Scarlet/Violet 2024 SIR, no reprints yet"),
    ("pop1-17", 0, "https://bulbapedia.bulbagarden.net/wiki/Tyranitar_ex_(POP_Series_1_17)", "POP Series 1 rare, exclusive"),
    ("ex15-10", 0, "https://bulbapedia.bulbagarden.net/wiki/Snorlax_%CE%B4_(Dragon_Frontiers_10)", "Dragon Frontiers delta Pokemon, no reprints"),
    ("ex10-102", 0, "https://bulbapedia.bulbagarden.net/wiki/Espeon_ex_(Unseen_Forces_102)", "EX Unseen Forces EX, no reprints"),
    ("sv8pt5-144", 0, "https://bulbapedia.bulbagarden.net/wiki/Leafeon_ex_(Prismatic_Evolutions_144)", "Scarlet/Violet 2025 SIR, no reprints yet"),
    ("ecard1-12", 0, "https://bulbapedia.bulbagarden.net/wiki/Feraligatr_(Expedition_Base_Set_12)", "e-card Expedition Rare Holo, exclusive"),
    ("hgss4-97", 0, "https://bulbapedia.bulbagarden.net/wiki/Mew_(HS%E2%80%94Triumphant_97)", "HGSS Triumphant Rare Prime, no reprints"),
    ("sm11-221", 0, "https://bulbapedia.bulbagarden.net/wiki/Raichu_%26_Alolan_Raichu-GX_(Unified_Minds_221)", "SM Tag Team GX, no reprints"),
    ("ex15-97", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_ex_%CE%B4_(Dragon_Frontiers_97)", "Dragon Frontiers delta EX, no reprints"),
    ("ex15-96", 0, "https://bulbapedia.bulbagarden.net/wiki/Latios_ex_%CE%B4_(Dragon_Frontiers_96)", "Dragon Frontiers delta EX, no reprints"),
    ("ecard1-40", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_(Expedition_Base_Set_40)", "e-card Expedition rare, exclusive"),
    ("bw8-132", 0, "https://bulbapedia.bulbagarden.net/wiki/Articuno-EX_(Plasma_Storm_132)", "BW Plasma Storm EX, no reprints"),
    ("bwp-BW74", 0, "https://bulbapedia.bulbagarden.net/wiki/Giratina_(BW_Black_Star_Promo_BW74)", "BW Black Star Promo, no reprints"),
    ("base6-39", 1, "https://bulbapedia.bulbagarden.net/wiki/Dark_Wartortle_(Legendary_Collection_39)", "Legendary Collection Uncommon reprint"),
    ("pl2-108", 0, "https://bulbapedia.bulbagarden.net/wiki/Infernape_E4_LV.X_(Rising_Rivals_108)", "Diamond/Pearl LV.X era, no reprints"),
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
    for card_id, flag, url, note in BATCH_11_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 11 (25 cards) complete.")
    print(f"Updated: {len(BATCH_11_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
