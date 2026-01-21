import os
import json
from dotenv import load_dotenv, find_dotenv
from supabase import create_client, Client

# Load environment variables
_ = load_dotenv(find_dotenv())
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

def create_schema():
    """Create tables for recipes using SQL via Supabase RPC"""
    
    schema_sql = """
    -- ============================================
    -- MAIN TABLES
    -- ============================================
    
    -- Recipes table
    CREATE TABLE IF NOT EXISTS recipes (
        id BIGSERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        source_url TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Enhanced ingredients table with parsed data
    CREATE TABLE IF NOT EXISTS ingredients (
        id BIGSERIAL PRIMARY KEY,
        recipe_id BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
        
        -- Original text
        original_text TEXT NOT NULL,
        
        -- Parsed components
        ingredient_name TEXT NOT NULL,
        quantity NUMERIC,
        unit TEXT,
        preparation TEXT,
        
        -- Categorization
        category TEXT, -- 'proteins', 'vegetables', 'grains', 'dairy', 'herbs', 'other'
        
        -- Metadata
        position INT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Instructions table
    CREATE TABLE IF NOT EXISTS instructions (
        id BIGSERIAL PRIMARY KEY,
        recipe_id BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
        step_number INT NOT NULL,
        instruction_text TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Nutrition table
    CREATE TABLE IF NOT EXISTS nutrition (
        id BIGSERIAL PRIMARY KEY,
        recipe_id BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
        serving TEXT,
        calories TEXT,
        carbohydrates TEXT,
        protein TEXT,
        fat TEXT,
        fiber TEXT,
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
    
    -- ============================================
    -- TAGGING SYSTEM
    -- ============================================
    
    -- Tags table (for proteins, dietary restrictions, cuisines, etc.)
    CREATE TABLE IF NOT EXISTS tags (
        id BIGSERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL, -- 'protein', 'dietary', 'cuisine', 'meal_type', 'cooking_method'
        description TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Recipe-Tag relationship (many-to-many)
    CREATE TABLE IF NOT EXISTS recipe_tags (
        id BIGSERIAL PRIMARY KEY,
        recipe_id BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
        tag_id BIGINT REFERENCES tags(id) ON DELETE CASCADE,
        confidence NUMERIC DEFAULT 1.0, -- How confident we are in this tag (0-1)
        auto_generated BOOLEAN DEFAULT false, -- Was this auto-tagged or manual?
        created_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(recipe_id, tag_id)
    );
    
    -- ============================================
    -- INDEXES FOR PERFORMANCE
    -- ============================================
    
    -- Ingredient indexes
    CREATE INDEX IF NOT EXISTS idx_ingredients_recipe ON ingredients(recipe_id);
    CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(ingredient_name);
    CREATE INDEX IF NOT EXISTS idx_ingredients_category ON ingredients(category);
    
    -- Instruction indexes
    CREATE INDEX IF NOT EXISTS idx_instructions_recipe ON instructions(recipe_id);
    
    -- Nutrition indexes
    CREATE INDEX IF NOT EXISTS idx_nutrition_recipe ON nutrition(recipe_id);
    
    -- Tag indexes
    CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category);
    CREATE INDEX IF NOT EXISTS idx_recipe_tags_recipe ON recipe_tags(recipe_id);
    CREATE INDEX IF NOT EXISTS idx_recipe_tags_tag ON recipe_tags(tag_id);
    
    -- Full-text search indexes
    CREATE INDEX IF NOT EXISTS idx_recipes_title_search 
        ON recipes USING gin(to_tsvector('english', title));
    CREATE INDEX IF NOT EXISTS idx_recipes_description_search 
        ON recipes USING gin(to_tsvector('english', description));
    CREATE INDEX IF NOT EXISTS idx_ingredients_name_search 
        ON ingredients USING gin(to_tsvector('english', ingredient_name));
    CREATE INDEX IF NOT EXISTS idx_ingredients_text_search 
        ON ingredients USING gin(to_tsvector('english', original_text));
    
    -- ============================================
    -- SEED COMMON TAGS
    -- ============================================
    
    -- Insert common protein tags
    INSERT INTO tags (name, category, description) VALUES
        ('chicken', 'protein', 'Contains chicken'),
        ('beef', 'protein', 'Contains beef'),
        ('pork', 'protein', 'Contains pork'),
        ('fish', 'protein', 'Contains fish'),
        ('seafood', 'protein', 'Contains seafood (shrimp, prawns, etc)'),
        ('lamb', 'protein', 'Contains lamb'),
        ('turkey', 'protein', 'Contains turkey'),
        ('tofu', 'protein', 'Contains tofu'),
        ('eggs', 'protein', 'Contains eggs'),
        ('vegetarian', 'dietary', 'Suitable for vegetarians'),
        ('vegan', 'dietary', 'Suitable for vegans'),
        ('gluten-free', 'dietary', 'Gluten-free recipe'),
        ('dairy-free', 'dietary', 'Dairy-free recipe'),
        ('low-carb', 'dietary', 'Low carbohydrate recipe'),
        ('keto', 'dietary', 'Keto-friendly recipe'),
        ('breakfast', 'meal_type', 'Breakfast dish'),
        ('lunch', 'meal_type', 'Lunch dish'),
        ('dinner', 'meal_type', 'Dinner dish'),
        ('snack', 'meal_type', 'Snack or appetizer'),
        ('dessert', 'meal_type', 'Dessert')
    ON CONFLICT (name) DO NOTHING;
    
    -- ============================================
    -- HELPER FUNCTIONS
    -- ============================================
    
    -- Function to auto-tag recipes based on ingredients
    CREATE OR REPLACE FUNCTION auto_tag_recipe(recipe_id_param BIGINT)
    RETURNS void AS $$
    DECLARE
        ingredient_text TEXT;
        tag_record RECORD;
    BEGIN
        -- Get all ingredient names for this recipe
        FOR ingredient_text IN 
            SELECT ingredient_name FROM ingredients WHERE recipe_id = recipe_id_param
        LOOP
            -- Check against protein tags
            FOR tag_record IN 
                SELECT id, name FROM tags WHERE category = 'protein'
            LOOP
                IF ingredient_text ILIKE '%' || tag_record.name || '%' THEN
                    -- Insert tag if not exists
                    INSERT INTO recipe_tags (recipe_id, tag_id, auto_generated, confidence)
                    VALUES (recipe_id_param, tag_record.id, true, 0.9)
                    ON CONFLICT (recipe_id, tag_id) DO NOTHING;
                END IF;
            END LOOP;
        END LOOP;
        
        -- Check for vegetarian (no meat proteins)
        IF NOT EXISTS (
            SELECT 1 FROM recipe_tags rt
            JOIN tags t ON rt.tag_id = t.id
            WHERE rt.recipe_id = recipe_id_param 
            AND t.name IN ('chicken', 'beef', 'pork', 'fish', 'seafood', 'lamb', 'turkey')
        ) THEN
            INSERT INTO recipe_tags (recipe_id, tag_id, auto_generated, confidence)
            SELECT recipe_id_param, id, true, 0.8
            FROM tags WHERE name = 'vegetarian'
            ON CONFLICT (recipe_id, tag_id) DO NOTHING;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    
    -- ============================================
    -- USEFUL VIEWS
    -- ============================================
    
    -- View: Recipes with their tags
    CREATE OR REPLACE VIEW recipe_tags_view AS
    SELECT 
        r.id as recipe_id,
        r.title,
        r.description,
        array_agg(DISTINCT t.name) FILTER (WHERE t.category = 'protein') as proteins,
        array_agg(DISTINCT t.name) FILTER (WHERE t.category = 'dietary') as dietary_tags,
        array_agg(DISTINCT t.name) FILTER (WHERE t.category = 'meal_type') as meal_types,
        array_agg(DISTINCT t.name) as all_tags
    FROM recipes r
    LEFT JOIN recipe_tags rt ON r.id = rt.recipe_id
    LEFT JOIN tags t ON rt.tag_id = t.id
    GROUP BY r.id, r.title, r.description;
    
    -- View: Ingredient summary by category
    CREATE OR REPLACE VIEW ingredient_categories_view AS
    SELECT 
        r.id as recipe_id,
        r.title,
        i.category,
        array_agg(i.ingredient_name ORDER BY i.position) as ingredients
    FROM recipes r
    JOIN ingredients i ON r.id = i.recipe_id
    WHERE i.category IS NOT NULL
    GROUP BY r.id, r.title, i.category;
    """
    
    print("="*70)
    print("SUPABASE RECIPE DATABASE SCHEMA")
    print("="*70)
    print("\n📋 This schema includes:")
    print("  ✓ Enhanced ingredients table with parsed data")
    print("  ✓ Tagging system for proteins and dietary restrictions")
    print("  ✓ Auto-tagging function")
    print("  ✓ Full-text search indexes")
    print("  ✓ Helpful views for querying")
    print("\n" + "="*70)
    print("\n⚠️  IMPORTANT: Copy and paste this SQL into your Supabase SQL Editor:\n")
    print(schema_sql)
    print("\n" + "="*70)
    
    # Save to file for convenience
    with open('supabase_schema.sql', 'w') as f:
        f.write(schema_sql)
    print("\n✓ Schema also saved to 'supabase_schema.sql'")
    
    input("\nPress Enter after you've run the SQL in Supabase...")
    
    return schema_sql


def get_example_queries():
    """Return example queries for using the schema"""
    
    examples = """
    -- ============================================
    -- EXAMPLE QUERIES
    -- ============================================
    
    -- 1. Find all pork recipes
    SELECT * FROM recipe_tags_view
    WHERE 'pork' = ANY(proteins);
    
    -- 2. Find all chicken recipes that are also low-carb
    SELECT r.title, rtv.proteins, rtv.dietary_tags
    FROM recipe_tags_view rtv
    JOIN recipes r ON rtv.recipe_id = r.id
    WHERE 'chicken' = ANY(rtv.proteins)
    AND 'low-carb' = ANY(rtv.dietary_tags);
    
    -- 3. Find vegetarian recipes
    SELECT * FROM recipe_tags_view
    WHERE 'vegetarian' = ANY(dietary_tags);
    
    -- 4. Get all recipes with their protein breakdown
    SELECT 
        r.title,
        string_agg(DISTINCT i.ingredient_name, ', ') as protein_ingredients
    FROM recipes r
    JOIN ingredients i ON r.id = i.recipe_id
    WHERE i.category = 'proteins'
    GROUP BY r.id, r.title;
    
    -- 5. Find recipes by multiple proteins (e.g., surf and turf)
    SELECT r.title, rtv.proteins
    FROM recipe_tags_view rtv
    JOIN recipes r ON rtv.recipe_id = r.id
    WHERE rtv.proteins && ARRAY['beef', 'seafood']::text[];
    
    -- 6. Search recipes by ingredient
    SELECT DISTINCT r.title
    FROM recipes r
    JOIN ingredients i ON r.id = i.recipe_id
    WHERE i.ingredient_name ILIKE '%garlic%';
    
    -- 7. Get recipe count by protein type
    SELECT 
        t.name as protein,
        COUNT(DISTINCT rt.recipe_id) as recipe_count
    FROM tags t
    JOIN recipe_tags rt ON t.id = rt.tag_id
    WHERE t.category = 'protein'
    GROUP BY t.name
    ORDER BY recipe_count DESC;
    
    -- 8. Full-text search across titles and descriptions
    SELECT title, description
    FROM recipes
    WHERE to_tsvector('english', title || ' ' || COALESCE(description, '')) 
          @@ to_tsquery('english', 'pizza & garlic');
    
    -- 9. Find recipes missing tags (need manual review)
    SELECT r.id, r.title
    FROM recipes r
    LEFT JOIN recipe_tags rt ON r.id = rt.recipe_id
    WHERE rt.id IS NULL;
    
    -- 10. Get complete recipe with all details
    SELECT 
        r.*,
        json_agg(DISTINCT i.*) as ingredients,
        json_agg(DISTINCT ins.*) as instructions,
        json_agg(DISTINCT n.*) as nutrition,
        array_agg(DISTINCT t.name) as tags
    FROM recipes r
    LEFT JOIN ingredients i ON r.id = i.recipe_id
    LEFT JOIN instructions ins ON r.id = ins.recipe_id
    LEFT JOIN nutrition n ON r.id = n.recipe_id
    LEFT JOIN recipe_tags rt ON r.id = rt.recipe_id
    LEFT JOIN tags t ON rt.tag_id = t.id
    WHERE r.id = 1
    GROUP BY r.id;
    """
    
    print("\n" + "="*70)
    print("EXAMPLE QUERIES")
    print("="*70)
    print(examples)
    
    # Save to file
    with open('example_queries.sql', 'w') as f:
        f.write(examples)
    print("\n✓ Examples saved to 'example_queries.sql'")


def test_connection():
    """Test Supabase connection"""
    try:
        # Try to query recipes table
        result = supabase.table('recipes').select('count').execute()
        print("\n✓ Successfully connected to Supabase!")
        return True
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nMake sure:")
        print("  1. SUPABASE_URL and SUPABASE_API_KEY are set in .env")
        print("  2. The schema has been created in Supabase SQL Editor")
        return False


if __name__ == "__main__":
    print("="*70)
    print("SUPABASE RECIPE DATABASE SETUP")
    print("="*70)
    
    # Check credentials
    if not SUPABASE_URL or not SUPABASE_API_KEY:
        print("\n⚠️  Missing credentials!")
        print("\nCreate a .env file with:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_API_KEY=your_supabase_anon_key")
        exit(1)
    
    # Step 1: Create schema
    print("\n📝 Step 1: Create Database Schema")
    create_schema()
    
    # Step 2: Test connection
    print("\n🔌 Step 2: Test Connection")
    if test_connection():
        print("\n✓ Setup complete!")
        
        # Step 3: Show example queries
        print("\n📚 Step 3: Example Queries")
        get_example_queries()
        
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("1. Import your recipe JSONs using the import script")
        print("2. Run auto_tag_recipe() function on each recipe")
        print("3. Query recipes by protein type using the views")
        print("4. Try the example queries in 'example_queries.sql'")
        print("="*70)
    else:
        print("\n⚠️  Please create the schema first, then run this script again.")