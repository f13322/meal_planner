def format_plan_to_markdown(plan: dict, currency: str) -> str:
    """
    Converts the structured plan dictionary into a clean Markdown string for export.
    """
    if not plan:
        return ""
    
    md = []
    md.append(f"# 🍲 Custom Meal Plan")
    md.append(f"**Estimated Total Cost:** {currency} {plan.get('estimated_total_cost', 0):.2f}\n")
    md.append("---")
    
    md.append("## 📅 Daily Schedule")
    for day, meals in plan.get("meals", {}).items():
        md.append(f"### {day}")
        for meal_type, meal_info in meals.items():
            md.append(f"- **{meal_type}:** {meal_info.get('name', 'N/A')}")
        md.append("")  # Empty line
        
    md.append("---")
    md.append("## 🛒 Shopping Checklist")
    grocery_list = plan.get("grocery_list", [])
    if grocery_list:
        for item in grocery_list:
            item_name = item.get("item", "")
            item_price = item.get("estimated_price", 0.0)
            md.append(f"- [ ] {item_name} (~ {currency} {item_price:.2f})")
    else:
        md.append("No ingredients listed.")
        
    return "\n".join(md)

def format_recipe_to_markdown(recipe: dict) -> str:
    """
    Converts a recipe dictionary into a Markdown string for display or export.
    """
    if not recipe:
        return ""
    
    md = []
    md.append(f"**{recipe.get('name')} Details:**\n\n")
    md.append(f"*Ingredients:*\n")

    for ingredient in recipe.get("ingredients", []):
        md.append(f"- {ingredient}\n")

    md.append(f"\n*Steps:*\n")
    for idx, step in enumerate(recipe.get("instructions", [])):
        md.append(f"{idx+1}. {step}\n")

    return "".join(md)