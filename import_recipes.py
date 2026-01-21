"""
Recipe JSON Import Script for Supabase
Imports recipe JSONs with ingredient parsing and auto-tagging
"""

import os
import json
from pathlib import Path
from fractions import Fraction
from dotenv import load_dotenv, find_dotenv
from supabase import create_client, Client

# Import your custom parsing utilities
from utils import parse_ingredient_advanced, categorize_ingredient

# Load environment variables
_ = load_dotenv(find_dotenv())
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)


# ============================================
# RECIPE IMPORT
# ============================================

def convert_quantity(quantity):
    """Convert Fraction objects to float for JSON serialization"""
    if quantity is None:
        return None
    
    if isinstance(quantity, Fraction):
        return float(quantity)
    
    if isinstance(quantity, (int, float)):
        return float(quantity)
    
    # Try to parse string quantities like "1/2"
    if isinstance(quantity, str):
        try:
            # Try direct conversion
            return float(quantity)
        except ValueError:
            try:
                # Try as fraction
                return float(Fraction(quantity))
            except (ValueError, ZeroDivisionError):
                return None
    
    return None


def convert_unit(unit):
    """Convert Unit objects to string for JSON serialization"""
    if unit is None:
        return ''
    
    # If it's already a string, return it
    if isinstance(unit, str):
        return unit
    
    # If it has a string representation, use it
    if hasattr(unit, '__str__'):
        return str(unit)
    
    # Try to get text attribute (some Unit objects have this)
    if hasattr(unit, 'text'):
        return unit.text
    
    # Last resort - convert to string
    try:
        return str(unit)
    except:
        return ''


def insert_recipe(recipe_data):
    """Insert a single recipe with all related data"""
    
    try:
        # Insert main recipe
        recipe_result = supabase.table('recipes').insert({
            'title': recipe_data['title'],
            'description': recipe_data.get('description', ''),
            'source_url': recipe_data.get('source_url', '')
        }).execute()
        
        recipe_id = recipe_result.data[0]['id']
        print(f"✓ Inserted recipe: {recipe_data['title']} (ID: {recipe_id})")
        
        # Parse and insert ingredients
        if 'ingredients' in recipe_data:
            ingredients_list = recipe_data['ingredients'].get('Ingredients', [])
            parsed_ingredients = []
            
            for idx, ingredient_text in enumerate(ingredients_list, 1):
                # Parse the ingredient using your custom utils
                parsed = parse_ingredient_advanced(ingredient_text)
                
                # Handle both dict and string returns from your parser
                if isinstance(parsed, str):
                    # Your fallback returns just the word
                    ingredient_name = parsed
                    quantity = None
                    unit = ''
                    preparation = ''
                else:
                    # Full parse result
                    ingredient_name = parsed.get('name', parsed.get('text', ''))
                    quantity = parsed.get('quantity')
                    unit = parsed.get('unit', '')
                    preparation = parsed.get('preparation', '')
                
                # Convert Fraction to float and Unit to string for JSON serialization
                quantity = convert_quantity(quantity)
                unit = convert_unit(unit)
                
                # Categorize it using your custom function
                category = categorize_ingredient(ingredient_name)
                
                parsed_ingredients.append({
                    'recipe_id': recipe_id,
                    'original_text': ingredient_text,
                    'ingredient_name': ingredient_name,
                    'quantity': quantity,
                    'unit': unit,
                    'preparation': preparation,
                    'category': category,
                    'position': idx
                })
            
            if parsed_ingredients:
                supabase.table('ingredients').insert(parsed_ingredients).execute()
                print(f"  ✓ Inserted {len(parsed_ingredients)} ingredients")
                
                # Show a sample of parsed ingredients for verification
                if parsed_ingredients:
                    sample = parsed_ingredients[0]
                    print(f"    Sample: {sample['original_text']}")
                    print(f"      → name: {sample['ingredient_name']}, category: {sample['category']}")
        
        # Insert instructions
        if 'instructions' in recipe_data:
            instructions_data = [
                {
                    'recipe_id': recipe_id,
                    'step_number': idx,
                    'instruction_text': inst
                }
                for idx, inst in enumerate(recipe_data['instructions'], 1)
            ]
            
            if instructions_data:
                supabase.table('instructions').insert(instructions_data).execute()
                print(f"  ✓ Inserted {len(instructions_data)} instructions")
        
                    # Insert nutrition
            if 'nutrition' in recipe_data:
                nutrition_data = {
                    'recipe_id': recipe_id,
                    **{
                        k.replace(' ', '_'): v
                        for k, v in recipe_data['nutrition'].items()
                    }
                }

                supabase.table('nutrition').insert(nutrition_data).execute()
                print("  ✓ Inserted nutrition data")
                    
        return recipe_id
        
    except Exception as e:
        print(f"✗ Error inserting recipe '{recipe_data.get('title', 'Unknown')}': {e}")
        import traceback
        traceback.print_exc()
        return None


def auto_tag_recipe(recipe_id):
    """Call the database function to auto-tag a recipe"""
    try:
        supabase.rpc('auto_tag_recipe', {'recipe_id_param': recipe_id}).execute()
        print(f"  ✓ Auto-tagged recipe {recipe_id}")
    except Exception as e:
        print(f"  ⚠️  Auto-tagging skipped (function may not exist): {e}")


def import_recipes_from_directory(directory_path, auto_tag=True):
    """Import all JSON files from a directory"""
    
    # Find all JSON files
    json_files = list(Path(directory_path).glob('*.json'))
    
    if not json_files:
        print(f"⚠️  No JSON files found in: {directory_path}")
        return
    
    print(f"\nFound {len(json_files)} recipe files")
    print("="*70)
    
    success_count = 0
    failed_recipes = []
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                recipe_data = json.load(f)
            
            recipe_id = insert_recipe(recipe_data)
            
            if recipe_id:
                success_count += 1
                
                # Auto-tag if requested
                if auto_tag:
                    auto_tag_recipe(recipe_id)
            else:
                failed_recipes.append(filepath.name)
                
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in {filepath.name}: {e}")
            failed_recipes.append(filepath.name)
        except Exception as e:
            print(f"✗ Error reading {filepath.name}: {e}")
            failed_recipes.append(filepath.name)
    
    print("="*70)
    print(f"\n✓ Successfully imported {success_count}/{len(json_files)} recipes")
    
    if failed_recipes:
        print(f"\n✗ Failed recipes ({len(failed_recipes)}):")
        for name in failed_recipes:
            print(f"  - {name}")
    
    return success_count, failed_recipes


def import_single_recipe(json_path, auto_tag=True):
    """Import a single recipe JSON file"""
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            recipe_data = json.load(f)
        
        recipe_id = insert_recipe(recipe_data)
        
        if recipe_id and auto_tag:
            auto_tag_recipe(recipe_id)
        
        return recipe_id
        
    except Exception as e:
        print(f"✗ Error importing {json_path}: {e}")
        return None


def show_import_stats():
    """Display statistics about imported recipes"""
    
    try:
        # Count recipes
        recipes = supabase.table('recipes').select('id', count='exact').execute()
        recipe_count = recipes.count
        
        # Count ingredients
        ingredients = supabase.table('ingredients').select('id', count='exact').execute()
        ingredient_count = ingredients.count
        
        # Count tags
        tags = supabase.table('recipe_tags').select('id', count='exact').execute()
        tag_count = tags.count
        
        print("\n" + "="*70)
        print("DATABASE STATISTICS")
        print("="*70)
        print(f"Total Recipes:     {recipe_count}")
        print(f"Total Ingredients: {ingredient_count}")
        print(f"Total Tags:        {tag_count}")
        print("="*70)
        
    except Exception as e:
        print(f"⚠️  Could not fetch stats: {e}")



# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("="*70)
    print("RECIPE IMPORT SCRIPT")
    print("="*70)
    
    # Check credentials
    if not SUPABASE_URL or not SUPABASE_API_KEY:
        print("\n⚠️  Missing credentials!")
        print("\nCreate a .env file with:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_API_KEY=your_supabase_anon_key")
        exit(1)
    
    recipes_dir = "recipes"
    
    if not recipes_dir:
        recipes_dir = "."
    
    # Verify directory exists
    if not os.path.isdir(recipes_dir):
        print(f"\n✗ Directory not found: {recipes_dir}")
        exit(1)
    
    # Ask about auto-tagging

    
    # Import recipes
    print(f"\nStarting import from: {recipes_dir}")
    #success_count, failed = import_recipes_from_directory(recipes_dir, auto_tag=True)
    import_single_recipe("oven-baked-barbecue-pork-ribs.json", auto_tag=True)
    print("done")
    # Show stats
    #if success_count > 0:
    #    show_import_stats()
        
    #     print("\n" + "="*70)
    #     print("NEXT STEPS:")
    #     print("="*70)
    #     print("1. View your recipes in Supabase Table Editor")
    #     print("2. Query by protein: SELECT * FROM recipe_tags_view WHERE 'chicken' = ANY(proteins);")
    #     print("3. Search ingredients: See example_queries.sql")
    #     print("="*70)
    
    # print("\n✓ Import complete!")