#!/usr/bin/env python3
"""
Job 1 Batch 7: Research cards 151-175 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
Rule: flag=1 ONLY with concrete evidence of specific re-release.
Default to flag=0 when in doubt.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_7_RESEARCH = [
    # Rows 152-176 of reprint_check.csv (cards 151-175)
    ("smp-SM78", 0, "https://bulbapedia.bulbagarden.net/wiki/Champions_Festival_(SM_Black_Star_Promo_SM78)", "SM Black Star Promo, no reprints"),
    ("sm12-221", 0, "https://bulbapedia.bulbagarden.net/wiki/Arceus_%26_Dialga_%26_Palkia-GX_(Cosmic_Eclipse_221)", "SM Cosmic Eclipse Tag Team GX, no reprints"),
    ("swshp-SWSH177", 0, "https://bulbapedia.bulbagarden.net/wiki/Special_Delivery_Bidoof_(SWSH_Black_Star_Promo_SWSH177)", "Sword/Shield Black Star Promo, no reprints"),
    ("rsv10pt5-173", 0, "https://bulbapedia.bulbagarden.net/wiki/Reshiram_ex_(White_Flare_173)", "Recent 2025 set, no reprints yet"),
    ("ex7-96", 0, "https://bulbapedia.bulbagarden.net/wiki/Rocket%27s_Articuno_ex_(Team_Rocket_Returns_96)", "Team Rocket Returns EX, no reprints"),
    ("ex9-96", 0, "https://bulbapedia.bulbagarden.net/wiki/Milotic_ex_(Emerald_96)", "EX Emerald era EX, no reprints"),
    ("ecard3-H26", 0, "https://bulbapedia.bulbagarden.net/wiki/Raikou_(Skyridge_H26)", "e-card Holo Rare, era exclusive"),
    ("np-39", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_ex_(Nintendo_Black_Star_Promo_39)", "Nintendo Black Star Promo, no reprints"),
    ("bw8-137", 0, "https://bulbapedia.bulbagarden.net/wiki/Blastoise_(Plasma_Storm_137)", "BW Plasma Storm Secret Rare, no reprints"),
    ("dc1-15", 0, "https://bulbapedia.bulbagarden.net/wiki/Team_Magma%27s_Groudon-EX_(Double_Crisis_15)", "Double Crisis EX, no reprints"),
    ("neo3-14", 0, "https://bulbapedia.bulbagarden.net/wiki/Suicune_(Neo_Revelation_14)", "Neo Revelation exclusive"),
    ("sm5-151", 0, "https://bulbapedia.bulbagarden.net/wiki/Lillie_(Ultra_Prism_151)", "SM Ultra Prism Rare Ultra, no reprints"),
    ("ex12-83", 0, "https://bulbapedia.bulbagarden.net/wiki/Arcanine_ex_(Legend_Maker_83)", "Legend Maker EX, no reprints"),
    ("pop5-3", 0, "https://bulbapedia.bulbagarden.net/wiki/Mew_%CE%B4_(POP_Series_5_3)", "POP Series 5 delta, exclusive"),
    ("base4-4", 1, "https://bulbapedia.bulbagarden.net/wiki/Charizard_(Base_Set_2_4)", "Base Set 2 is reprint set, has reprints"),
    ("sm12-215", 0, "https://bulbapedia.bulbagarden.net/wiki/Blastoise_%26_Piplup-GX_(Cosmic_Eclipse_215)", "SM Tag Team GX, no reprints"),
    ("ecard3-H23", 0, "https://bulbapedia.bulbagarden.net/wiki/Politoed_(Skyridge_H23)", "e-card Holo Rare, era exclusive"),
    ("ecard2-H25", 0, "https://bulbapedia.bulbagarden.net/wiki/Suicune_(Aquapolis_H25)", "e-card Holo Rare, era exclusive"),
    ("neo3-66", 0, "https://bulbapedia.bulbagarden.net/wiki/Shining_Magikarp_(Neo_Revelation_66)", "Shining Pokemon exclusive to Neo"),
    ("sm12-143a", 0, "https://bulbapedia.bulbagarden.net/wiki/Togepi_%26_Cleffa_%26_Igglybuff-GX_(Cosmic_Eclipse_143a)", "SM Tag Team GX, no reprints"),
    ("base5-4", 0, "https://bulbapedia.bulbagarden.net/wiki/Dark_Charizard_(Team_Rocket_4)", "Team Rocket Dark Charizard, no reprints"),
    ("pl3-143", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_G_LV.X_(Supreme_Victors_143)", "Diamond/Pearl LV.X era, no reprints"),
    ("si1-1", 0, "https://bulbapedia.bulbagarden.net/wiki/Mew_(Southern_Islands_1)", "Southern Islands set promo, exclusive"),
    ("neo4-12", 0, "https://bulbapedia.bulbagarden.net/wiki/Light_Arcanine_(Neo_Destiny_12)", "Neo Destiny exclusive"),
    ("neo1-18", 0, "https://bulbapedia.bulbagarden.net/wiki/Typhlosion_(Neo_Genesis_18)", "Neo Genesis exclusive"),
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
    for card_id, flag, url, note in BATCH_7_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 7 (25 cards) complete.")
    print(f"Updated: {len(BATCH_7_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
