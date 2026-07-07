#!/usr/bin/env python3
"""
Job 1 Batch 2: Research cards 26-50 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
New rule: flag=1 ONLY with concrete evidence of specific re-release.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_2_RESEARCH = [
    # Rows 27-51 of reprint_check.csv
    ("sm9-165", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_%26_Mimikyu-GX_(Team_Up_170)", "GX-era Tag Team, no reprints found"),
    ("sv8pt5-161", 0, "https://bulbapedia.bulbagarden.net/wiki/Umbreon_ex_(Prismatic_Evolutions_161)", "Recent promo-only release, no reprints"),
    ("np-5", 0, "https://bulbapedia.bulbagarden.net/wiki/Mudkip_(Nintendo_Black_Star_Promo_5)", "Black Star Promo, unique release"),
    ("bwp-BW28", 0, "https://bulbapedia.bulbagarden.net/wiki/Tropical_Beach_(BW_Black_Star_Promo_28)", "BW Black Star Promo, one-time release"),
    ("ex8-106", 0, "https://bulbapedia.bulbagarden.net/wiki/Latios_★_(Deoxys_106)", "Star Pokémon exclusive"),
    ("neo4-112", 0, "https://bulbapedia.bulbagarden.net/wiki/Shining_Steelix_(Neo_Destiny_112)", "Shining Pokémon exclusive to Neo"),
    ("ex6-108", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_ex_(FireRed_%26_LeafGreen_108)", "EX-era card, no reprints"),
    ("ecard3-H1", 0, "https://bulbapedia.bulbagarden.net/wiki/Alakazam_(Skyridge_H1)", "e-card Holo, era exclusive"),
    ("ecard2-H29", 0, "https://bulbapedia.bulbagarden.net/wiki/Umbreon_(Aquapolis_H29)", "e-card era, exclusive"),
    ("ex12-90", 0, "https://bulbapedia.bulbagarden.net/wiki/Regice_★_(Legend_Maker_90)", "Star Pokémon exclusive"),
    ("ecard3-H10", 0, "https://bulbapedia.bulbagarden.net/wiki/Gyarados_(Skyridge_H10)", "e-card, era exclusive"),
    ("basep-41", 0, "https://bulbapedia.bulbagarden.net/wiki/Lucky_Stadium_(Wizards_Black_Star_Promo_41)", "1999 promo, unique"),
    ("ex13-102", 0, "https://bulbapedia.bulbagarden.net/wiki/Gyarados_★_δ_(Holon_Phantoms_102)", "Delta Pokémon exclusive"),
    ("swsh7-218", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_VMAX_(Evolving_Skies_218)", "Evolving Skies done printing"),
    ("bw8-136", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_(Plasma_Storm_136)", "Secret rare BW-era, no reprints"),
    ("basep-40", 0, "https://bulbapedia.bulbagarden.net/wiki/Pokémon_Center_(Wizards_Black_Star_Promo_40)", "1999 promo, unique"),
    ("ex10-114", 0, "https://bulbapedia.bulbagarden.net/wiki/Raikou_★_(Unseen_Forces_114)", "Star Pokémon exclusive"),
    ("ex10-115", 0, "https://bulbapedia.bulbagarden.net/wiki/Suicune_★_(Unseen_Forces_115)", "Star Pokémon exclusive"),
    ("sv4pt5-232", 0, "https://bulbapedia.bulbagarden.net/wiki/Mew_ex_(Paldean_Fates_232)", "Recent special set, no reprints"),
    ("svp-85", 0, "https://bulbapedia.bulbagarden.net/wiki/Pikachu_with_Grey_Felt_Hat_(Scarlet_%26_Violet_Black_Star_Promo_85)", "SV-era promo, unique"),
    ("ex14-99", 0, "https://bulbapedia.bulbagarden.net/wiki/Alakazam_★_(Crystal_Guardians_99)", "Star Pokémon exclusive"),
    ("swsh8-271", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_VMAX_(Fusion_Strike_271)", "Fusion Strike done printing"),
    ("ex11-111", 0, "https://bulbapedia.bulbagarden.net/wiki/Groudon_★_(Delta_Species_111)", "Delta Pokémon exclusive"),
    ("xy2-108", 0, "https://bulbapedia.bulbagarden.net/wiki/M_Charizard-EX_(Flashfire_108)", "Secret rare XY-era, no reprints"),
    ("ecard3-H11", 0, "https://bulbapedia.bulbagarden.net/wiki/Houndoom_(Skyridge_H11)", "e-card, era exclusive"),
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
    for card_id, flag, url, note in BATCH_2_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 2 (25 cards) complete.")
    print(f"Updated: {len(BATCH_2_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
