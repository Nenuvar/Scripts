# file: generate_encounter.py

import json
import random
import re
from pathlib import Path
from typing import List
from datetime import datetime

CR_XP = {
    "0": 10, "1/8": 25, "1/4": 50, "1/2": 100,
    "1": 200, "2": 450, "3": 700, "4": 1100, "5": 1800,
    "6": 2300, "7": 2900, "8": 3900, "9": 5000,
    "10": 5900, "11": 7200, "12": 8400, "13": 10000,
    "14": 11500, "15": 13000, "16": 15000, "17": 18000,
    "18": 20000, "19": 22000, "20": 25000
}

XP_THRESHOLDS = {
    1:  [25, 50, 75, 100],
    2:  [50, 100, 150, 200],
    3:  [75, 150, 225, 400],
    4:  [125, 250, 375, 500],
    5:  [250, 500, 750, 1100],
    6:  [300, 600, 900, 1400],
    7:  [350, 750, 1100, 1700],
    8:  [450, 900, 1400, 2100],
    9:  [550, 1100, 1600, 2400],
    10: [600, 1200, 1900, 2800],
    11: [800, 1600, 2400, 3600],
    12: [1000, 2000, 3000, 4500],
    13: [1100, 2200, 3400, 5100],
    14: [1250, 2500, 3800, 5700],
    15: [1400, 2800, 4300, 6400],
    16: [1600, 3200, 4800, 7200],
    17: [2000, 3900, 5900, 8800],
    18: [2100, 4200, 6300, 9500],
    19: [2400, 4900, 7300, 10900],
    20: [2800, 5700, 8500, 12700]
}


def load_party():
    with open("party.json") as f:
        return json.load(f)


def load_bestiary():
    with open("bestiary-mm.json") as f:
        return json.load(f)["monster"]


def get_xp_threshold(level: int, count: int, difficulty: str) -> int:
    index = {"easy": 0, "medium": 1, "hard": 2, "deadly": 3}[difficulty]
    return XP_THRESHOLDS[level][index] * count


def normalize_cr(cr_field):
    if isinstance(cr_field, str):
        return cr_field
    elif isinstance(cr_field, dict):
        return str(cr_field.get("value", "0"))
    return "0"


def build_encounter(monsters: List[dict], budget: int, main_quest: bool) -> List[dict]:
    pool = []
    for m in monsters:
        cr_str = normalize_cr(m.get("cr"))
        xp = CR_XP.get(cr_str)
        if xp:
            m["_cr_str"] = cr_str
            pool.append((m, xp))

    random.shuffle(pool)
    encounter = []

    if main_quest:
        pool.sort(key=lambda x: x[1], reverse=True)
        for m, xp in pool:
            if xp <= budget * 0.7:
                encounter.append(m)
                budget -= xp
                break
        random.shuffle(pool)

    total = sum(CR_XP[m["_cr_str"]] for m in encounter)
    for m, xp in pool:
        if m not in encounter and total + xp <= budget:
            encounter.append(m)
            total += xp
        if total >= budget * 0.9:
            break
    return encounter


def random_encounter_name():
    adjectives = ["Bloody", "Silent", "Burning", "Twisted", "Shattered", "Cursed", "Forgotten"]
    nouns = ["Oath", "Throne", "Marsh", "Beast", "Vault", "Coven", "Wound"]
    return f"The {random.choice(adjectives)} {random.choice(nouns)}"


def slugify(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def get_monster_links(vault_path: Path) -> dict:
    links = {}
    for md_file in vault_path.rglob("*.md"):
        key = md_file.stem.replace('-', ' ').lower()
        slug = md_file.stem
        links[key] = slug
    return links


def write_markdown(encounter, monsters, monster_links):
    now = datetime.now().strftime("%Y-%m-%d")
    safe_name = encounter["name"].replace(" ", "_").replace("/", "_")
    filename = f"{now}_{safe_name}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"title: {encounter['name']}\n")
        f.write(f"type: {encounter['type'].title()} Quest\n")
        f.write(f"environment: {encounter['environment'].title()}\n")
        f.write(f"date: {now}\n")
        f.write("tags: [encounter, dnd5e]\n")
        f.write("obsidianUIMode: preview\n")
        f.write("cssclasses: json5e-monster\n")
        sources = [m.get('source', '?') for m in monsters]
        f.write(f"sources: {', '.join(sources)}\n")
        f.write("---\n\n")

        f.write(f"# {encounter['name']}\n\n")

        for monster in monsters:
            name_key = monster["name"].lower()
            slug = monster_links.get(name_key)
            if slug:
                monster_link = f"[[{slug}|{monster['name']}]]"
            else:
                monster_link = f"[[{monster['name']}]]"

            f.write(f"# {monster_link}\n")
            if monster.get("description"):
                f.write(monster["description"] + "\n\n")
            f.write("## Statblock\n")
            f.write("```ad-statblock\n")
            f.write(f"title: {monster['name']}\n")
            f.write(f"*{monster.get('size', '?')} {monster.get('type', '?')}, {monster.get('alignment', '?')}*\n\n")
            f.write(f"{monster.get('ac', '?')}\n")
            f.write(f"- **Speed** {monster.get('speed', '?')}\n\n")
            f.write("|STR|DEX|CON|INT|WIS|CHA|\n")
            f.write("|:---:|:---:|:---:|:---:|:---:|:---:|\n")
            f.write(f"|{monster.get('str', '?')}|{monster.get('dex', '?')}|{monster.get('con', '?')}|{monster.get('int', '?')}|{monster.get('wis', '?')}|{monster.get('cha', '?')}|\n\n")
            f.write(f"- **Proficiency Bonus** {monster.get('pb', '—')}\n")
            f.write(f"- **Saving Throws** {monster.get('save', '—')}\n")
            f.write(f"- **Skills** {monster.get('skill', '—')}\n")
            f.write(f"- **Senses** {monster.get('senses', '')}, passive Perception {monster.get('passive', '?')}\n")
            f.write(f"- **Languages** {monster.get('languages', '—')}\n")
            f.write(f"- **Challenge** {monster.get('cr', '?')}\n")
            f.write("```\n")

    print(f"\nSaved encounter to {filename}")


def main():
    vault_path = Path(r"\\svgkomm.svgdrift.no\Users\sk5049835\Documents\Notater\Obsidian\DM")
    monster_links = get_monster_links(vault_path)

    while True:
        party = load_party()
        bestiary = load_bestiary()

        level = int(party['members'][0]['level'])
        count = len(party['members'])

        quest_type = input("Is this a main quest or a side quest? ").strip().lower()
        main_quest = quest_type == "main"
        difficulty = "deadly" if main_quest else "medium"
        budget = get_xp_threshold(level, count, difficulty)

        env_input = input("Where will the heroes fight? ").strip().lower()
        matching = [m for m in bestiary if env_input in [e.lower() for e in m.get("environment", [])]]

        if not matching:
            all_envs = set(e for m in bestiary for e in m.get("environment", []))
            print("\nThere are no monsters in this location.")
            print("Available environments:")
            for env in sorted(all_envs):
                print(f" - {env}")
            continue

        selected = build_encounter(matching, budget, main_quest)
        encounter = {
            "name": random_encounter_name(),
            "type": quest_type,
            "environment": env_input,
        }

        print(f"\n== Encounter Generated ==")
        print(f"Name: {encounter['name']}")
        print(f"Type: {encounter['type']}")
        print(f"Environment: {encounter['environment']}")
        print("Monsters:")
        for m in selected:
            print(f" - {m['name']} (CR {m.get('_cr_str', normalize_cr(m.get('cr')))})")

        choice = input("\nDo you want to save this encounter or create a new one? (save/new/exit): ").strip().lower()
        if choice == "save":
            write_markdown(encounter, selected, monster_links)
            break
        elif choice == "new":
            continue
        elif choice == "exit":
            print("Exiting without saving.")
            break
        else:
            print("Invalid input. Please enter 'save', 'new', or 'exit'.")
            continue


if __name__ == "__main__":
    main()
