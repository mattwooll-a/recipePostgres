# Recipe Database Project 

A PostgreSQL-based recipe management system with ingredient parsing and automatic tagging. Recipe data is scraped from RecipeTin Eats (https://www.recipetineats.com/) for educational purposes.

## Overview

This project scrapes recipe JSON files into a relational database with:
- Parsed ingredients with quantities, units, and categories
- Automatic tagging by protein type and dietary restrictions
- Full-text search capabilities
- Nutrition information tracking

## Setup

### Requirements

- Python 3.8 or higher
- Supabase account (free tier)

### Installation

Install required packages:

```bash
pip install supabase python-dotenv ingredient-parser-nlp BeautifulSoup
```

### Configuration

1. Create a Supabase project at https://supabase.com
2. Copy your project URL and API key from Settings > API
3. Create a `.env` file with your credentials:

```
SUPABASE_URL=your_project_url
SUPABASE_API_KEY=your_anon_key
```

### Scraping 

1. run the web scraping tool 
```bash
python batchcreate.py
```

### Database Setup

1. Run the schema generator:
```bash
python supabase_schema.py
```

2. Copy the generated SQL and paste it into Supabase SQL Editor

3. Execute the SQL to create tables

### Import Recipes

Run the import script:

```bash
python import_recipes.py
```

Enter the path to your recipe JSON files when prompted.

## Project Structure

```
recipe-database/
├── .env                    # Supabase credentials
├── utils.py               # Ingredient parsing functions
├── supabase_schema.py     # Database schema generator
├── import_recipes.py      # Recipe import script
├── example_queries.sql    # Sample SQL queries
└── recipes/               # Recipe JSON files
```

## Recipe JSON Format

```json
{
  "title": "Recipe Name",
  "description": "Recipe description",
  "ingredients": {
    "Ingredients": [
      "2 cups flour",
      "1 tsp salt"
    ]
  },
  "instructions": [
    "Step 1",
    "Step 2"
  ],
  "nutrition": {
    "calories": "200cal",
    "protein": "5g"
  },
  "source_url": "https://www.recipetineats.com/..."
}
```

## Database Schema

### Tables

- **recipes** - Recipe metadata
- **ingredients** - Parsed ingredient data with categories
- **instructions** - Step-by-step instructions
- **nutrition** - Nutritional information
- **tags** - Searchable tags for filtering
- **recipe_tags** - Links recipes to tags

### Ingredient Categories

Ingredients are automatically categorized as:
- proteins (chicken, beef, pork, fish, eggs, tofu)
- vegetables
- grains
- dairy
- herbs
- spices
- other

## Example Queries

Find all pork recipes:
```sql
SELECT * FROM recipe_tags_view 
WHERE 'pork' = ANY(proteins);
```

Find vegetarian recipes:
```sql
SELECT * FROM recipe_tags_view
WHERE 'vegetarian' = ANY(dietary_tags);
```

Search by ingredient:
```sql
SELECT DISTINCT r.title
FROM recipes r
JOIN ingredients i ON r.id = i.recipe_id
WHERE i.ingredient_name ILIKE '%garlic%';
```

Count recipes by protein type:
```sql
SELECT t.name, COUNT(rt.recipe_id) as count
FROM tags t
JOIN recipe_tags rt ON t.id = rt.tag_id
WHERE t.category = 'protein'
GROUP BY t.name
ORDER BY count DESC;
```

## How It Works

### Ingredient Parsing

Input: "2 pork cutlets, sliced (200g each)"

Output:
- name: pork cutlets
- quantity: 2.0
- unit: cutlets
- preparation: sliced
- category: proteins

### Auto-Tagging

After import, recipes are automatically tagged based on their ingredients:
- Contains pork → tagged as "pork"
- No meat → tagged as "vegetarian"
- Contains eggs → tagged as "eggs"

## Customization

Add custom ingredient categories in `utils.py`:

```python
INGREDIENT_CATEGORIES = {
    'proteins': ['chicken', 'beef', 'pork'],
    'your_category': ['ingredient1', 'ingredient2']
}
```

Add custom tags via SQL:

```sql
INSERT INTO tags (name, category, description) VALUES
('paleo', 'dietary', 'Paleo-friendly recipe');
```

## Data Source and Usage

All recipe data is scraped from RecipeTin Eats for educational and personal use only. IF YOU MODIFY THE SCRAPPING TOOL, PLEASE BE RESPECTFUL (right now there is a random multisecond delay, always keep some form of rate limiting)

Allowed:
- Personal learning and practice!
- Portfolio projects!
- Experimentation with data!

Not Allowed:
- Commercial use without permission
- Redistribution of recipe data
- Claiming recipes as original work

Please visit RecipeTin Eats (https://www.recipetineats.com/) for the original recipes and support the creator. (Again nagi has a great site I only did this so i would have a dataset i would actually use)

## Resources

- Supabase: https://supabase.com/docs
- PostgreSQL: https://www.postgresql.org/docs/
- RecipeTin Eats: https://www.recipetineats.com/
- ingredient-parser-nlp: https://github.com/strangetom/ingredient-parser

## License

Code is provided for educational purposes. Recipe content belongs to RecipeTin Eats.

## Acknowledgments

- Nagi Maehashi and RecipeTin Eats for the recipes!!!!
- Supabase for database hosting
- ingredient-parser-nlp library for parsing functionality