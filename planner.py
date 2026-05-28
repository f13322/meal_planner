import os
import json
from google import genai
from google.genai import types
import time

class MealPlanner:
    def __init__(self):
        # google-genai automatically uses the GEMINI_API_KEY environment variable.
        # We perform an explicit check here to provide a clear error message if it's missing.
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Initialize the modern unified GenAI Client
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"

    def generate_plan(
        self, 
        user_message: str, 
        chat_history: list, 
        constraints: dict, 
        current_plan: dict, 
        local_recipes: dict
    ) -> dict:
        """
        Evaluates the conversational intent (generate fresh vs. adjust existing)
        and outputs the appropriate structured meal plan.
        """
        prompt = f"""
        You are a professional meal planning assistant. You must either generate a brand-new meal plan or modify the existing one based on the user's request.

        System Constraints (Sidebar Settings):
        - Days: {constraints.get('days', 3)}
        - Budget Limit: {constraints.get('budget_limit', 'Flexible')} {constraints.get('currency', 'NZD')}
        - Dietary Restrictions: {', '.join(constraints.get('dietary_restrictions', [])) or 'None'}
        - Allergies: {', '.join(constraints.get('allergies', [])) or 'None'}
        - Country: {constraints.get('country', 'New Zealand')}

        Current Active Plan (If any is displayed):
        {json.dumps(current_plan) if current_plan else "None (No plan generated yet)"}

        Recent Chat Conversation History:
        {json.dumps(chat_history[-5:])}

        User's New Message:
        "{user_message}"

        Known Local Recipes (Prioritize using these recipes if they match constraints):
        {json.dumps(list(local_recipes.keys()))}

        INSTRUCTIONS:
        1. INTENT CLASSIFICATION:
           - If the user asks to "start over", "generate a new plan", "reset", or if there is no "Current Active Plan", discard the old plan and generate a completely new plan.
           - If the user provides additional/new constraints in their message (e.g., "start over but make it keto instead"), merge those conversational constraints into the System Constraints.
           - If the user is asking to modify, replace, swap, or tweak the "Current Active Plan" (e.g., "change Wednesday's dinner"), preserve all other unchanged meals exactly as they are and only modify the requested parts.

        2. FEASIBILITY EVALUATION:
           - Assess whether the requested plan is realistic under the budget, duration, and country.
           - If the budget is unrealistic, set "is_feasible" to false, explain why in "feasibility_explanation", and suggest a realistic adjustment. Generate a "best-effort" plan anyway.

        Output MUST be valid JSON matching this exact structure:
        {{
            "is_feasible": true,
            "feasibility_explanation": "",
            "meals": {{
            "Day 1": {{
              "Breakfast": {{"name": "Meal Name", "ingredients": ["ing 1", "ing 2"]}},
              "Lunch": {{"name": "Meal Name", "ingredients": ["ing 1", "ing 2"]}},
              "Dinner": {{"name": "Meal Name", "ingredients": ["ing 1", "ing 2"]}}
            }}
            }},
            "estimated_total_cost": 45.0,
            "grocery_list": [
            {{"item": "item name", "estimated_price": 3.50}}
            ]
        }}
        Do not include any extra text or markdown formatting outside of raw JSON.
        """
        e = ''
        for attempt in range(5):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                return json.loads(response.text)
            except Exception as e:
                print(f"Generation attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2**attempt)  # Brief pause before retrying to avoid API rate limits or transient issues
            break
        return {
                "is_feasible": True,
                "feasibility_explanation": "",
                "meals": {},
                "estimated_total_cost": 0.0,
                "grocery_list": [],
                "error": f"Planning processing failed: {str(e)}"
            }

    def fetch_recipe_details(self, meal_name: str) -> dict:
        """
        Fetches recipe steps and exact ingredients using Gemini's knowledge.
        """
        prompt = f"""
        Provide a standard recipe for '{meal_name}'.
        Output must be valid JSON matching this structure:
        {{
          "name": "{meal_name}",
          "ingredients": ["ingredient 1", "ingredient 2"],
          "instructions": ["Step 1", "Step 2"],
          "dietary_tags": ["tag1", "tag2"]
        }}
        Return raw JSON only.
        """
        
        response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
        return json.loads(response.text)