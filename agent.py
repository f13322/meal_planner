from memory import MemoryManager
from planner import MealPlanner
from validator import PlanValidator

class MealAgent:
    def __init__(self):
        self.memory = MemoryManager()
        self.planner = MealPlanner()
        self.validator = PlanValidator()

    def process_input(self, user_message: str, constraints: dict) -> tuple[str, dict]:
        """
        Processes conversation inputs and returns (text_response, updated_plan_dict).
        """
        # Sync constraints to local memory profile
        self.memory.save_profile({
            "dietary_restrictions": constraints.get("dietary_restrictions", []),
            "allergies": constraints.get("allergies", []),
            "budget_limit": constraints.get("budget_limit"),
            "currency": constraints.get("currency", "NZD"),
            "country": constraints.get("country", "New Zealand"),
            "days": constraints.get("days", 3)
        })

        chat_history = []
        # Add the incoming user message to local history
        chat_history.append({"role": "user", "content": user_message})

        local_recipes = self.memory.get_recipes()
        current_plan = constraints.get("current_plan")

        # Invoke the unified, context-aware generator/modifier
        new_plan = self.planner.generate_plan(
            user_message=user_message,
            chat_history=chat_history,
            constraints=constraints,
            current_plan=current_plan,
            local_recipes=local_recipes
        )

        if "error" in new_plan:
            return f"Sorry, I couldn't process that: {new_plan['error']}", {}

        # Programmatic Validation Check
        is_valid, violations = self.validator.validate(new_plan, constraints)

        # Self-correction pass if violations occur
        while not is_valid:
            correction_prompt = (
                f"The plan violated standard rules: {', '.join(violations)}. "
                f"Please adjust only the problematic items to respect these restrictions."
            )
            new_plan = self.planner.generate_plan(
                user_message=correction_prompt,
                chat_history=chat_history,
                constraints=constraints,
                current_plan=new_plan,
                local_recipes=local_recipes
            )
            is_valid, violations = self.validator.validate(new_plan, constraints)

        self._cache_new_recipes(new_plan)


        response_text = "Here is a new meal plan structured to match your parameters."
        if not is_valid:
            response_text += f" (Constraint Warnings: {', '.join(violations)})"

        # Save assistant turn to chat history
        chat_history.append({"role": "assistant", "content": response_text})

        return response_text, new_plan

    def _cache_new_recipes(self, plan_data: dict):
        local_recipes = self.memory.get_recipes()
        for day, meals in plan_data.get("meals", {}).items():
            for meal_type, meal_info in meals.items():
                meal_name = meal_info.get("name", "")
                if meal_name and meal_name.lower() not in local_recipes:
                    recipe_details = self.planner.fetch_recipe_details(meal_name)
                    if recipe_details.get("ingredients"):
                        self.memory.save_recipe(meal_name, recipe_details)

    def get_recipe(self, meal_name: str) -> dict:
        local_recipes = self.memory.get_recipes()
        meal_key = meal_name.lower()
        if meal_key in local_recipes:
            return local_recipes[meal_key]
        
        recipe_details = self.planner.fetch_recipe_details(meal_name)
        if recipe_details.get("ingredients"):
            self.memory.save_recipe(meal_name, recipe_details)
        return recipe_details