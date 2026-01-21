from utils import *
if __name__ == "__main__":
    # Test parsing
    test_ingredients = [
        "2 pork cutlets , at room temperature (200g/7oz each, bone in)",
        "1 tbsp lemon pepper",
        "2 tbsp olive oil , separated",
        "2 zucchinis , sliced",
        "1/2 cup couscous",
        "50 g / 1.5 oz feta cheese"
    ]
    
    print("PARSING EXAMPLES:")
    print("="*60)
    
    for ing in test_ingredients:
        parsed = parse_ingredient_advanced(ing)
        category = categorize_ingredient(parsed['name'])        
        print(f"\nOriginal: {ing}")
        print(f"  Name: {parsed['name']}")
        print(f"  Quantity: {parsed['quantity']}")
        print(f"  Unit: {parsed['unit']}")
        print(f"  Preparation: {parsed['preparation']}")
        print(f"  Category: {category}")
        print(f"  ✓ Valid: {parsed['parsed_successfully']}")