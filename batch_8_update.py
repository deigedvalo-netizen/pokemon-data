#!/usr/bin/env python3
"""
Job 1 Batch 8: Research cards 176-200 from reprint_check.csv
Findings based on Bulbapedia research + TCG knowledge.
Rule: flag=1 ONLY with concrete evidence of specific re-release.
Default to flag=0 when in doubt.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_8_RESEARCH = [
    # Rows 177-201 of reprint_check.csv (cards 176-200)
    ("pop5-12", 0, "https://bulbapedia.bulbagarden.net/wiki/Pikachu_(POP_Series_5_12)", "POP Series 5 exclusive"),
    ("ex6-104", 0, "https://bulbapedia.bulbagarden.net/wiki/Blastoise_ex_(FireRed_%26_LeafGreen_104)", "FireRed & LeafGreen EX, no reprints"),
    ("neo3-8", 0, "https://bulbapedia.bulbagarden.net/wiki/Houndoom_(Neo_Revelation_8)", "Neo Revelation exclusive"),
    ("base3-4", 0, "https://bulbapedia.bulbagarden.net/wiki/Dragonite_(Fossil_4)", "Fossil Set era rare, no reprints"),
    ("sv2-203", 0, "https://bulbapedia.bulbagarden.net/wiki/Magikarp_(Paldea_Evolved_203)", "Scarlet/Violet Illustration Rare, no reprints"),
    ("bw5-106", 0, "https://bulbapedia.bulbagarden.net/wiki/Groudon-EX_(Dark_Explorers_106)", "BW Dark Explorers EX, no reprints"),
    ("neo4-4", 0, "https://bulbapedia.bulbagarden.net/wiki/Dark_Espeon_(Neo_Destiny_4)", "Neo Destiny exclusive"),
    ("gym1-4", 0, "https://bulbapedia.bulbagarden.net/wiki/Erika%27s_Dragonair_(Gym_Heroes_4)", "Gym Heroes exclusive"),
    ("neo2-12", 0, "https://bulbapedia.bulbagarden.net/wiki/Tyranitar_(Neo_Discovery_12)", "Neo Discovery exclusive"),
    ("bw6-120", 0, "https://bulbapedia.bulbagarden.net/wiki/Mew-EX_(Dragons_Exalted_120)", "BW Dragons Exalted EX, no reprints"),
    ("ecard3-H31", 0, "https://bulbapedia.bulbagarden.net/wiki/Vaporeon_(Skyridge_H31)", "e-card Holo Rare, era exclusive"),
    ("bw5-107", 0, "https://bulbapedia.bulbagarden.net/wiki/Darkrai-EX_(Dark_Explorers_107)", "BW Dark Explorers EX, no reprints"),
    ("ex7-15", 0, "https://bulbapedia.bulbagarden.net/wiki/Dark_Dragonite_(Team_Rocket_Returns_15)", "Team Rocket Returns rare, no reprints"),
    ("ecard3-H15", 0, "https://bulbapedia.bulbagarden.net/wiki/Machamp_(Skyridge_H15)", "e-card Holo Rare, era exclusive"),
    ("base5-3", 0, "https://bulbapedia.bulbagarden.net/wiki/Dark_Blastoise_(Team_Rocket_3)", "Team Rocket Dark Blastoise, no reprints"),
    ("xy7-96", 0, "https://bulbapedia.bulbagarden.net/wiki/Primal_Kyogre-EX_(Ancient_Origins_96)", "XY Ancient Origins Secret Rare, no reprints"),
    ("sv3pt5-199", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_ex_(151_199)", "Scarlet/Violet 151 Special Illustration, no reprints"),
    ("pl4-97", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_LV.X_(Arceus_97)", "Diamond/Pearl LV.X era, no reprints"),
    ("ecard3-H7", 0, "https://bulbapedia.bulbagarden.net/wiki/Flareon_(Skyridge_H7)", "e-card Holo Rare, era exclusive"),
    ("base6-19", 1, "https://bulbapedia.bulbagarden.net/wiki/Zapdos_(Legendary_Collection_19)", "Legendary Collection Rare Holo reprint"),
    ("col1-SL7", 0, "https://bulbapedia.bulbagarden.net/wiki/Lugia_(Call_of_Legends_SL7)", "Call of Legends set, no reprints"),
    ("ecard1-19", 0, "https://bulbapedia.bulbagarden.net/wiki/Mew_(Expedition_Base_Set_19)", "e-card Mew, era exclusive"),
    ("swsh12pt5gg-GG69", 0, "https://bulbapedia.bulbagarden.net/wiki/Giratina_VSTAR_(Crown_Zenith_Galarian_Gallery_GG69)", "Sword/Shield Crown Zenith, no reprints"),
    ("swsh7-205", 0, "https://bulbapedia.bulbagarden.net/wiki/Leafeon_VMAX_(Evolving_Skies_205)", "Sword/Shield Evolving Skies VMAX Rainbow, no reprints"),
    ("sm12-222", 0, "https://bulbapedia.bulbagarden.net/wiki/Reshiram_%26_Zekrom-GX_(Cosmic_Eclipse_222)", "SM Tag Team GX, no reprints"),
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
    for card_id, flag, url, note in BATCH_8_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 8 (25 cards) complete.")
    print(f"Updated: {len(BATCH_8_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
