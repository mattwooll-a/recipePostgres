from utils import parse_ingredient_advanced

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
        print(parsed)