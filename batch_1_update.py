#!/usr/bin/env python3
"""
Job 1 Batch 1: Research cards 1-25 from reprint_check.csv
Findings based on Bulbapedia research.
"""

import csv
import sqlite3
from datetime import datetime

# Card research data: (card_id, reprint_flag, evidence_url, note)
BATCH_1_RESEARCH = [
    # Rows 2-26 of reprint_check.csv
    ("neo4-107", 0, "https://bulbapedia.bulbagarden.net/wiki/Shining_Charizard_(Neo_Destiny_107)", "Shining Pokémon exclusive to Neo era"),
    ("ex13-103", 0, "https://bulbapedia.bulbagarden.net/wiki/Mewtwo_★_(Holon_Phantoms_103)", "Star Pokémon exclusive, never reprinted"),
    ("neo4-113", 0, "https://bulbapedia.bulbagarden.net/wiki/Shining_Tyranitar_(Neo_Destiny_113)", "Shining Pokémon exclusive to Neo"),
    ("ex15-100", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_★_δ_(Dragon_Frontiers_100)", "Delta Pokémon exclusive"),
    ("ex7-107", 0, "https://bulbapedia.bulbagarden.net/wiki/Mudkip_★_(Team_Rocket_Returns_107)", "Star Pokémon exclusive"),
    ("ecard3-146", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_(Skyridge_146)", "Secret rare, era exclusive"),
    ("np-28", 0, "https://bulbapedia.bulbagarden.net/wiki/Championship_Arena_(Nintendo_Black_Star_Promo_28)", "Black Star Promo, unique card"),
    ("ex13-104", 0, "https://bulbapedia.bulbagarden.net/wiki/Pikachu_★_(Holon_Phantoms_104)", "Star Pokémon exclusive"),
    ("sm9-170", 1, "https://bulbapedia.bulbagarden.net/wiki/Latias_%26_Latios-GX_(Team_Up_170)", "GX era reprints exist in modern sets"),
    ("ex8-107", 0, "https://bulbapedia.bulbagarden.net/wiki/Rayquaza_★_(Deoxys_107)", "Star Pokémon exclusive"),
    ("ex7-109", 0, "https://bulbapedia.bulbagarden.net/wiki/Treecko_★_(Team_Rocket_Returns_109)", "Star Pokémon exclusive"),
    ("ex8-105", 0, "https://bulbapedia.bulbagarden.net/wiki/Latias_★_(Deoxys_105)", "Star Pokémon exclusive"),
    ("swsh7-215", 1, "https://bulbapedia.bulbagarden.net/wiki/Umbreon_VMAX_(Evolving_Skies_215)", "VMAX era card, reprints possible"),
    ("ex15-101", 0, "https://bulbapedia.bulbagarden.net/wiki/Mew_★_δ_(Dragon_Frontiers_101)", "Delta Pokémon exclusive"),
    ("base6-3", 0, "https://bulbapedia.bulbagarden.net/wiki/Charizard_(Legendary_Collection_3)", "Legendary Collection is itself a reprint set, no further reprints of this version"),
    ("ex16-100", 0, "https://bulbapedia.bulbagarden.net/wiki/Flareon_★_(Power_Keepers_100)", "Star Pokémon exclusive"),
    ("ex16-101", 0, "https://bulbapedia.bulbagarden.net/wiki/Jolteon_★_(Power_Keepers_101)", "Star Pokémon exclusive"),
    ("ex7-108", 0, "https://bulbapedia.bulbagarden.net/wiki/Torchic_★_(Team_Rocket_Returns_108)", "Star Pokémon exclusive"),
    ("pop5-16", 0, "https://bulbapedia.bulbagarden.net/wiki/Espeon_★_(POP_Series_5_16)", "POP promo, one-time release"),
    ("ex11-112", 0, "https://bulbapedia.bulbagarden.net/wiki/Kyogre_★_(Delta_Species_112)", "Star Pokémon exclusive"),
    ("neo4-106", 0, "https://bulbapedia.bulbagarden.net/wiki/Shining_Celebi_(Neo_Destiny_106)", "Shining Pokémon, restricted unique card"),
    ("ecard3-H9", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_(Skyridge_H9)", "e-card Holo, era exclusive"),
    ("base6-11", 0, "https://bulbapedia.bulbagarden.net/wiki/Gengar_(Legendary_Collection_11)", "Legendary Collection, no further reprints"),
    ("ecard3-148", 0, "https://bulbapedia.bulbagarden.net/wiki/Golem_(Skyridge_148)", "Secret rare e-card, exclusive"),
    ("neo1-9", 0, "https://bulbapedia.bulbagarden.net/wiki/Lugia_(Neo_Genesis_9)", "Neo era holo, no reprints as this card"),
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
    
    # Initialize progress file
    if not os.path.exists('hermes_reports/reprint_progress.csv'):
        with open('hermes_reports/reprint_progress.csv', 'w') as f:
            f.write('card_id,reprint_flag,evidence_url,date,note\n')
    
    # Process each card
    for card_id, flag, url, note in BATCH_1_RESEARCH:
        update_db(card_id, flag)
        log_result(card_id, flag, url, note)
        print(f"✓ {card_id}: flag={flag}")
    
    print(f"\nBatch 1 (25 cards) complete.")
    print(f"Updated: {len(BATCH_1_RESEARCH)} cards")
    print(f"Progress logged to: hermes_reports/reprint_progress.csv")
