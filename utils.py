import json
from pathlib import Path
from langchain_core.documents import Document
import os
from langchain.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

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
