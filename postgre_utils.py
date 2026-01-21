import os
import json
from supabase import create_client, Client

_ = load_dotenv(find_dotenv())
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_URL= os.getenv("SUPABASE_URL")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

def create_schema():
    """Create tables for recipes using SQL via Supabase RPC"""
    
    schema_sql = """
    -- Create recipes table
    CREATE TABLE IF NOT EXISTS recipes (
        id BIGSERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        source_url TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Create ingredients table
    CREATE TABLE IF NOT EXISTS ingredients (
        id BIGSERIAL PRIMARY KEY,
        recipe_id BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
        ingredient_text TEXT NOT NULL,
        position INT
    );

    -- Create instructions table
    CREATE TABLE IF NOT EXISTS instructions (
        id BIGSERIAL PRIMARY KEY,
        recipe_id BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
        step_number INT NOT NULL,
        instruction_text TEXT NOT NULL
    );

    -- Create nutrition table
    CREATE TABLE IF NOT EXISTS nutrition (
        id BIGSERIAL PRIMARY KEY,
        recipe_id BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
        serving TEXT,
        calories TEXT,
        carbohydrates TEXT,
        protein TEXT,
        fat TEXT,
        saturated_fat TEXT,
        polyunsaturated_fat TEXT,
        cholesterol TEXT,
        sodium TEXT,
        potassium TEXT,
        sugar TEXT,
        vitamin_a TEXT,
        vitamin_c TEXT,
        calcium TEXT,
        iron TEXT
    );

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_ingredients_recipe ON ingredients(recipe_id);
    CREATE INDEX IF NOT EXISTS idx_instructions_recipe ON instructions(recipe_id);
    CREATE INDEX IF NOT EXISTS idx_nutrition_recipe ON nutrition(recipe_id);
    
    -- Enable full-text search on recipes
    CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes USING gin(to_tsvector('english', title));
    CREATE INDEX IF NOT EXISTS idx_ingredients_text ON ingredients USING gin(to_tsvector('english', ingredient_text));
    """
    
    print("⚠️  Note: Schema creation needs to be done via Supabase SQL Editor")
    print("Copy and paste this SQL into your Supabase SQL Editor:\n")
    print(schema_sql)
    print("\n" + "="*60)
    input("Press Enter after you've run the SQL in Supabase...")