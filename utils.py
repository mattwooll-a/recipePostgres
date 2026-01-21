import json
from pathlib import Path
from langchain_core.documents import Document
import os
from langchain.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from ingredient_parser import parse_ingredient
import re


RECIPE_DIR = "./recipes"

def build_retriever(limit=10):
    docs = load_recipe_docs(limit=limit)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 5})

@tool
def load_full_recipe(title: str) -> dict:
    """
    Load the full recipe JSON (ingredients, instructions, nutrition)
    for a given recipe title.
    """
    filename = title.lower().replace(" ", "-") + ".json"
    path = os.path.join(RECIPE_DIR, filename)
    print(path)
    if not os.path.exists(path):
        return {"error": f"Recipe '{title}' not found."}

    with open(path, "r") as f:
        return json.load(f)

@tool
def get_recipe_stats(title: str) -> dict:
    """
    Return lightweight stats for a recipe without loading full content.
    """
    filename = title.lower().replace(" ", "-") + ".json"
    path = os.path.join(RECIPE_DIR, filename)

    if not os.path.exists(path):
        return {"error": f"Recipe '{title}' not found."}

    with open(path, "r") as f:
        data = json.load(f)

    ingredients = data.get("ingredients", {}).get("Ingredients", [])
    instructions = (
        data.get("ingredients", {}).get("Instructions", [])
        or data.get("instructions", [])
    )

    return {
        "title": title,
        "num_ingredients": len(ingredients),
        "num_steps": len(instructions),
        "has_slow_cooker": any(
            "slow cooker" in step.lower() for step in instructions
        )
    }

@tool
def get_recipe_nutrition(title: str) -> dict:
    """
    Return nutrition information for a recipe.
    """
    filename = title.lower().replace(" ", "-") + ".json"
    path = os.path.join(RECIPE_DIR, filename)

    if not os.path.exists(path):
        return {"error": f"Recipe '{title}' not found."}

    with open(path, "r") as f:
        data = json.load(f)

    return data.get("nutrition", {})



def load_recipe_docs(limit=10):
    docs = []
    files = list(Path("./recipes").glob("*.json"))

    for i, path in enumerate(files):
        if limit and i >= limit:
            break

        with open(path) as f:
            r = json.load(f)

        ingredients_flat = ", ".join(
            r["ingredients"].get("Ingredients", [])
        )

        content = f"""
Title: {r['title']}
Ingredients: {ingredients_flat}
"""

        docs.append(
            Document(
                page_content=content.strip(),
                metadata={
                    "title": r["title"],
                    "source": r["source_url"],
                    "path": str(path)
                }
            )
        )

    return docs

def parse_ingredient_advanced(ingredient_text):
    """
    Parse ingredient using NLP library
    Returns structured data: name, quantity, unit, preparation
    """
    try:
        parsed = parse_ingredient(ingredient_text)
        if parsed.name[0].confidence > 0.6:
            result = {
                'name': parsed.name[0].text if parsed.name else '',
                'quantity': parsed.amount[0].quantity if parsed.amount else None,
                'unit': parsed.amount[0].unit if parsed.amount else '',
                'preparation': parsed.preparation.text if parsed.preparation else '',
                'original': ingredient_text,
                'parsed_successfully': True
            }
            return result
        else:
            raise ValueError("low conf")
        
    except Exception as e:
        print(f"Parse failed for '{ingredient_text}': {e}")
        return fallback_parse(ingredient_text)

def fallback_parse(ingredient_text):
    """Simple regex-based parsing when NLP fails"""
    pattern = r'^[\d\/\.\s]+(tsp|tbsp|tablespoon|teaspoon|cup|cups|oz|ounce|ounces|g|gram|grams|kg|lb|lbs|pound|pounds|ml|milliliter|liter|l|small|large|medium|pinch|dash|clove|cloves)s?(\s*\/\s*[\d\/\.\s]+(tsp|tbsp|tablespoon|teaspoon|cup|cups|oz|ounce|ounces|g|gram|grams|kg|lb|lbs|pound|pounds|ml|milliliter|liter|l)s?)?\s+'
    
    cleaned = re.sub(pattern, '', ingredient_text, flags=re.IGNORECASE)
    
    if cleaned == ingredient_text:
        cleaned = re.sub(r'^[\d\/\.\s]+', '', ingredient_text).strip()
    
    main_part = re.split(r'[,(]', cleaned)[0].strip()
    
    main_part = re.sub(r'^[\/\s]+', '', main_part).strip()
    
    words = main_part.split()
    return words[0]

INGREDIENT_CATEGORIES = {
    'proteins': ['pork', 'chicken', 'beef', 'lamb', 'fish', 'salmon', 'tuna', 
                 'shrimp', 'prawns', 'tofu', 'eggs', 'turkey'],
    'vegetables': ['zucchini', 'capsicum', 'pepper', 'onion', 'garlic', 'tomato',
                   'carrot', 'broccoli', 'spinach', 'lettuce', 'mushroom'],
    'grains': ['couscous', 'rice', 'pasta', 'quinoa', 'bread', 'flour'],
    'dairy': ['cheese', 'feta', 'milk', 'butter', 'cream', 'yogurt'],
    'herbs': ['mint', 'basil', 'parsley', 'cilantro', 'thyme', 'rosemary']
}

def categorize_ingredient(ingredient_name):
    """Find which category an ingredient belongs to"""
    ingredient_lower = ingredient_name.lower()
    
    for category, keywords in INGREDIENT_CATEGORIES.items():
        for keyword in keywords:
            if keyword in ingredient_lower:
                return category
    
    return 'other'


