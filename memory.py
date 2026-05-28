import json
import os

def load_json(filepath, default_value):
    """
    Loads JSON data from a file, returns default_value if file doesn't exist or is invalid.
    """
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump(default_value, f, indent=2)
        return default_value
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default_value

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

class MemoryManager:
    def __init__(self):
        self.recipes = load_json("recipes.json", {})
        self.memory = load_json(
            "memory.json", 
            {
                "user_profile": {
                    "dietary_restrictions": [], 
                    "allergies": [], 
                    "budget_limit": None, 
                    "currency": "NZD", 
                    "country": "New Zealand",
                    "days": 3
                }, 
            }
        )

    def get_recipes(self):
        return self.recipes

    def save_recipe(self, name, recipe_data):
        self.recipes[name.lower()] = recipe_data
        save_json("recipes.json", self.recipes)

    def get_profile(self):
        return self.memory.get("user_profile", {})

    def save_profile(self, profile):
        self.memory["user_profile"] = profile
        save_json("memory.json", self.memory)