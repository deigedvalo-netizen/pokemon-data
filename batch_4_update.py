#!/usr/bin/env python3
"""
Job 1 Batch 4: Research cards 76-100 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
Rule: flag=1 ONLY with concrete evidence of specific re-release.
Default to flag=0 when in doubt.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_4_RESEARCH = [
    # Rows 77-101 of reprint_check.csv (cards 76-100)
    ("ex3-100", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_(Dragon_Frontiers_100)", "Dragon Frontiers secret rare, no confirmed reprints"),
    ("ru1-7", 0, "https://bulbapedia.bulbagarden.net/wiki/Pikachu_(Pok%C3%A9mon_Rumble_7)", "Rumble set, exclusive promotional product"),
    ("base6-2", 1, "https://bulbapedia.bulbagarden.net/wiki/Articuno_(Legendary_Collection_2)", "Legendary Collection is reprint of Base Set Articuno"),
    ("xy4-114", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar-EX_(Phantom_Forces_114)", "XY-era Secret Rare, no reprints"),
    ("ex12-91", 0, "https://bulbapedia.bulbagarden.net/wiki/Regirock_%E2%98%85_(Legend_Maker_91)", "Star Pokemon, EX-era exclusive"),
    ("base6-29", 1, "https://bulbapedia.bulbagarden.net/wiki/Mewtwo_(Legendary_Collection_29)", "Legendary Collection reprint of Base Set Mewtwo"),
    ("bw8-134", 0, "https://bulbapedia.bulbagarden.net/wiki/Lugia-EX_(Plasma_Storm_134)", "BW-era Plasma Storm, no reprints"),
    ("base1-4", 1, "https://bulbapedia.bulbagarden.net/wiki/Charizard_(Base_Set_4)", "Base Set Charizard reprinted in Base Set 2, Legendary Collection, multiple promos"),
    ("neo4-6", 0, "https://bulbapedia.bulbagarden.net/wiki/Dark_Gengar_(Neo_Destiny_6)", "Neo Destiny era exclusive"),
    ("ecard1-20", 0, "https://bulbapedia.bulbagarden.net/wiki/Mewtwo_(Expedition_Base_Set_20)", "e-card era, exclusive to Expedition"),
    ("bw9-122", 0, "https://bulbapedia.bulbagarden.net/wiki/Ultra_Ball_(Plasma_Freeze_122)", "BW-era Trainer Secret Rare, no reprints"),
    ("sm35-78", 0, "https://bulbapedia.bulbagarden.net/wiki/Mewtwo-GX_(Shining_Legends_78)", "Shining Legends set, no reprints"),
    ("dp7-103", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_(Stormfront_103)", "Diamond/Pearl era Secret Rare, no reprints"),
    ("ecard3-H30", 0, "https://bulbapedia.bulbagarden.net/wiki/Umbreon_(Skyridge_H30)", "e-card Holo Rare, era exclusive"),
    ("base6-64", 1, "https://bulbapedia.bulbagarden.net/wiki/Snorlax_(Legendary_Collection_64)", "Legendary Collection Uncommon, reprint of Base Set Snorlax"),
    ("bw6-128", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_(Dragons_Exalted_128)", "BW-era Secret Rare, no reprints"),
    ("pop4-1", 0, "https://bulbapedia.bulbagarden.net/wiki/Chimecho_%CE%B4_(POP_Series_4_1)", "POP Series 4 set, exclusive product"),
    ("sm10-205", 0, "https://bulbapedia.bulbagarden.net/wiki/Gardevoir_%26_Sylveon-GX_(Unbroken_Bonds_205)", "SM-era Tag Team GX, no reprints"),
    ("gym1-14", 0, "https://bulbapedia.bulbagarden.net/wiki/Sabrina%27s_Gengar_(Gym_Heroes_14)", "Gym Heroes era, exclusive"),
    ("ecard2-150", 0, "https://bulbapedia.bulbagarden.net/wiki/Nidoking_(Aquapolis_150)", "e-card Secret Rare, era exclusive"),
    ("ecard2-148", 0, "https://bulbapedia.bulbagarden.net/wiki/Kingdra_(Aquapolis_148)", "e-card Secret Rare, era exclusive"),
    ("svp-150", 0, "https://bulbapedia.bulbagarden.net/wiki/Paradise_Resort_(Scarlet_%26_Violet_Black_Star_Promo_150)", "SV Black Star Promo, no reprints"),
    ("hsp-HGSS18", 0, "https://bulbapedia.bulbagarden.net/wiki/Tropical_Tidal_Wave_(HGSS_Black_Star_Promo_HGSS18)", "HGSS Black Star Promo, no reprints"),
    ("base6-70", 1, "https://bulbapedia.bulbagarden.net/wiki/Charmander_(Legendary_Collection_70)", "Legendary Collection Common, reprint of Base Set Charmander"),
    ("bw7-145", 0, "https://bulbapedia.bulbagarden.net/wiki/Black_Kyurem-EX_(Boundaries_Crossed_145)", "BW-era EX, no reprints"),
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
    for card_id, flag, url, note in BATCH_4_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 4 (25 cards) complete.")
    print(f"Updated: {len(BATCH_4_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
