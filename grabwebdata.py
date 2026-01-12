import requests
from bs4 import BeautifulSoup
import time
import json
import re

def clean_text(el):
    if el is None:
        return ""
    return el.get_text(separator=" ", strip=True)

def sanitize_ingredient(text):
    if not text:
        return ""
    text = re.sub(r"[▢▪•◦◆■]", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s\.\,\-\(\)\/]", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def parse_ingredients(content_div):
    ingredients = {}
    current_section = None

    for el in content_div.find_all(["h3", "li"]):
        if el.name == "h3":
            heading = clean_text(el)

            # Only allow ingredient sections
            if "ingredient" in heading.lower():
                current_section = heading
                ingredients[current_section] = []
            else:
                current_section = None

        elif el.name == "li" and current_section:
            ingredients[current_section].append(
                sanitize_ingredient(clean_text(el))
            )

    return ingredients


def parse_instructions(content_div):
    instructions = []
    in_instructions = False

    for el in content_div.find_all(["h3", "li"]):
        if el.name == "h3":
            heading = clean_text(el).lower()
            in_instructions = "instruction" in heading

        elif el.name == "li" and in_instructions:
            instructions.append(clean_text(el))

    return instructions

def parse_nutrition(nutrition_div):
    nutrition = {}

    containers = nutrition_div.find_all(
        "span",
        class_=lambda c: c and "wprm-nutrition-label-text-nutrition-container" in c
    )

    for c in containers:
        label_el = c.find("span", class_="wprm-nutrition-label-text-nutrition-label")
        value_el = c.find("span", class_="wprm-nutrition-label-text-nutrition-value")
        unit_el  = c.find("span", class_="wprm-nutrition-label-text-nutrition-unit")
        daily_el = c.find("span", class_="wprm-nutrition-label-text-nutrition-daily")

        if not label_el or not value_el:
            continue

        key = label_el.get_text(strip=True).replace(":", "").lower()
        value = value_el.get_text(strip=True)
        unit = unit_el.get_text(strip=True) if unit_el else ""
        daily = daily_el.get_text(strip=True) if daily_el else ""

        nutrition[key] = {
            "value": value,
            "unit": unit,
            "daily": daily
        }
        key = re.sub(r"\s+", "_", key)
        nutrition_flat = {
            k: f"{v['value']}{v['unit']} {v['daily']}".strip()
            for k, v in nutrition.items()
        }

    return nutrition_flat


def extract_description(rec_div):
    texts = []

    for el in rec_div.find_all(["p", "div"], recursive=False):
        txt = clean_text(el)
        if not txt:
            continue
        if "ingredient" in txt.lower():
            break
        texts.append(txt)

    return " ".join(texts)

def pullfromurl(url):
    headers = {
        "User-Agent": "personalrecipecontainer/0.1 (contact: mattwooll.a@gmail.com)"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rec_div = soup.find("div", class_="wprm-entry-content")
    cal_div = soup.find("div", class_="wprm-entry-nutrition")
    name = url.split("/")[-1]

    recipe = {
        "title": soup.find("h1").get_text(strip=True),
        "description": extract_description(rec_div),
        "ingredients": parse_ingredients(rec_div),
        "instructions": parse_instructions(rec_div),
        "nutrition": parse_nutrition(cal_div),
        "source_url": url
    }


    with open((name + ".json"), "w", encoding="utf-8") as f:
        json.dump(recipe, f, indent=2, ensure_ascii=False)
    return recipe

def try_scrape_recipe(url):
    try:
        recipe = pullfromurl(url)
        if not recipe:
            return None
        if not recipe.get("ingredients"):
            return None
        return recipe
    except Exception as e:
        print(f"[FAIL] {url} -> {e}")
        return None

pullfromurl('https://www.recipetineats.com/oven-baked-barbecue-pork-ribs')