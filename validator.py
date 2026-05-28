import os
import json

RULES_FILE = "rules.json"

class PlanValidator:
    def __init__(self):
        # Default fallback configurations in case the JSON file is missing
        default_rules = {
            "non_vegetarian_keywords": ["chicken", "beef", "pork", "fish", "meat", "bacon"],
            "non_vegan_keywords": ["chicken", "beef", "pork", "fish", "meat", "milk", "butter", "cheese", "egg"],
            "gluten_keywords": ["wheat", "bread", "pasta", "flour"],
            "hidden_allergens": {
                "peanuts": ["peanut"],
                "dairy": ["milk", "butter", "cheese"]
            }
        }
        
        # Load from JSON with fallback handling
        self.rules = self._load_rules(default_rules)

    def _load_rules(self, fallback: dict) -> dict:
        """
        Loads validation rules from a JSON file, returns fallback if file is missing or invalid.
        """
        if not os.path.exists(RULES_FILE):
            # Write a default rules file if none exists
            with open(RULES_FILE, "w") as f:
                json.dump(fallback, f, indent=2)
            return fallback

        try:
            with open(RULES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return fallback


    def validate(self, plan_data: dict, constraints: dict) -> tuple[bool, list[str]]:
        """
        Validates the generated meal plan against budget, dietary, and allergy constraints.
        """
        violations = []
        
        # Budget Verification
        budget_limit = constraints.get("budget_limit")
        estimated_cost = plan_data.get("estimated_total_cost", 0)
        currency = constraints.get("currency", "NZD")
        
        if budget_limit and estimated_cost > budget_limit:
            violations.append(
                f"Estimated budget of {currency}{estimated_cost:.2f} exceeds your set limit of {currency}{budget_limit:.2f}."
            )

        # Grab and normalize constraints
        dietary_restrictions = [d.lower() for d in constraints.get("dietary_restrictions", [])]
        allergies = [a.lower() for a in constraints.get("allergies", [])]

        meals = plan_data.get("meals", {})
        if not meals:
            return False, ["The meal plan is empty or could not be generated."]

        # Individual Meal Verification
        for day, daily_meals in meals.items():
            for meal_type, meal_info in daily_meals.items():
                meal_name = meal_info.get("name", "").lower()
                ingredients = [i.lower() for i in meal_info.get("ingredients", [])]
                
                # Check dietary requirements
                meal_violations = self._check_dietary(day, meal_type, meal_name, ingredients, dietary_restrictions)
                violations.extend(meal_violations)

                # Check user-defined allergies
                allergy_violations = self._check_allergies(day, meal_type, meal_name, ingredients, allergies)
                violations.extend(allergy_violations)

        is_valid = len(violations) == 0
        return is_valid, violations

    def _check_dietary(self, day: str, meal_type: str, meal_name: str, ingredients: list, dietary_restrictions: list) -> list[str]:
        """
        Checks if the meal violates any of the user's dietary restrictions.
        """
        violations = []
        
        # Check Vegan Rules
        if "vegan" in dietary_restrictions:
            keywords = self.rules.get("non_vegan_keywords", [])
            for keyword in keywords:
                if self._keyword_match(keyword, meal_name, ingredients):
                    violations.append(
                        f"Non-Vegan item ({keyword}) identified in {day} {meal_type}: '{meal_name.title()}'."
                    )
                    break  # Trigger once per meal to avoid spamming the log
        
        # Check Vegetarian Rules (Only if Vegan isn't active, to avoid duplicates)
        elif "vegetarian" in dietary_restrictions:
            keywords = self.rules.get("non_vegetarian_keywords", [])
            for keyword in keywords:
                if self._keyword_match(keyword, meal_name, ingredients):
                    violations.append(
                        f"Non-Vegetarian item ({keyword}) identified in {day} {meal_type}: '{meal_name.title()}'."
                    )
                    break
                    
        # Check Gluten-Free Rules
        if "gluten-free" in dietary_restrictions or "gluten free" in dietary_restrictions:
            keywords = self.rules.get("gluten_keywords", [])
            for keyword in keywords:
                if self._keyword_match(keyword, meal_name, ingredients):
                    # Exception safety: skip checking if the meal or ingredients are explicitly labeled gluten-free
                    if "gluten-free" in meal_name or any("gluten-free" in ing or "gluten free" in ing for ing in ingredients):
                        continue
                    violations.append(
                        f"Gluten-containing item ({keyword}) identified in {day} {meal_type}: '{meal_name.title()}'."
                    )
                    break

        return violations

    def _check_allergies(self, day: str, meal_type: str, meal_name: str, ingredients: list, allergies: list) -> list[str]:
        """
        Checks if the meal contains any of the user's known allergens.
        """
        violations = []
        hidden_allergens = self.rules.get("hidden_allergens", {})
        
        for allergy in allergies:
            # Check if allergy exists in our loaded hidden allergen mapping
            keywords_to_check = [allergy]
            if allergy in hidden_allergens:
                keywords_to_check.extend(hidden_allergens[allergy])
                
            for keyword in keywords_to_check:
                if self._keyword_match(keyword, meal_name, ingredients):
                    violations.append(
                        f"Allergen warning! '{allergy.title()}' (found via matching term '{keyword}') detected in {day} {meal_type}: '{meal_name.title()}'."
                    )
                    break
        return violations

    def _keyword_match(self, keyword: str, meal_name: str, ingredients: list) -> bool:
        """
        Checks if a keyword matches a substring in either the meal name or ingredients.
        """
        if keyword in meal_name:
            return True
            
        for ingredient in ingredients:
            if keyword in ingredient:
                return True
                
        return False