# file: hero_encounter_cli.py

import json
import os
from pathlib import Path

def get_party_file():
    return Path.cwd() / "party.json"

def load_party(filepath):
    if not filepath.exists():
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def save_party(party, filepath):
    with open(filepath, 'w') as f:
        json.dump(party, f, indent=2)
    print(f"\nParty saved to {filepath.resolve()}")

def ask_party():
    party = {}
    party['party_name'] = input("What is the party name? ")
    num_heroes = int(input("How many heroes are there? "))
    heroes = []
    for i in range(num_heroes):
        print(f"\nHero #{i+1}:")
        name = input("  Name: ")
        race = input("  Race: ")
        klass = input("  Class: ")
        heroes.append({"name": name, "race": race, "class": klass})
    shared_level = input("\nWhat level are all the heroes? ")
    for hero in heroes:
        hero['level'] = shared_level
    party['members'] = heroes
    return party

def display_party(party):
    print(f"\nParty Name: {party['party_name']}")
    for hero in party['members']:
        print(f"  {hero['name']} - {hero['race']} {hero['class']} (Level {hero['level']})")

def ask_encounter():
    print("\n== Encounter Setup ==")
    location = input("Where is the encounter taking place? (e.g., swamp, desert, forest): ")
    encounter_type = input("Is this a main encounter or side quest? ").strip().lower()
    monster_wish = input("Any special monster wishes? (Leave blank if none): ")
    return {
        "location": location,
        "type": encounter_type,
        "monster_wish": monster_wish or None
    }

def main():
    print("== Hero Encounter CLI Tool ==")
    FILEPATH = get_party_file()
    party = None

    if FILEPATH.exists():
        use_existing = input("Load existing party? [Y/n]: ").strip().lower()
        if use_existing in ('', 'y', 'yes'):
            party = load_party(FILEPATH)
            print("\n== Loaded Party ==")
            display_party(party)

    if not party:
        print("\n== Create New Party ==")
        party = ask_party()
        save_party(party, FILEPATH)
        print("\n== Party Saved ==")
        display_party(party)

    encounter = ask_encounter()

    print("\n== Final Encounter Summary ==")
    display_party(party)
    print(f"\nEncounter at: {encounter['location']}")
    print(f"Type: {encounter['type']}")
    if encounter['monster_wish']:
        print(f"Special Monster: {encounter['monster_wish']}")
    else:
        print("No specific monster preference.")

if __name__ == '__main__':
    main()
