import streamlit as st
from helpers import format_plan_to_markdown, format_recipe_to_markdown
from dotenv import load_dotenv

# Initialize Env vars
load_dotenv()

from agent import MealAgent


st.set_page_config(page_title="Meal Agent", layout="wide", initial_sidebar_state="expanded")

# Safe initialization of our orchestrator agent
if "agent" not in st.session_state:
    try:
        st.session_state.agent = MealAgent()
    except ValueError as e:
        st.error(f"Setup Error: {e}. Please add a valid GEMINI_API_KEY inside your `.env` file.")
        st.stop()

# Initialize conversational logs and plan memory
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your meal planning agent. Tell me what kind of meal plan you are looking for."}
    ]

if "current_plan" not in st.session_state:
    st.session_state.current_plan = None

st.title("🍲 Meal Planning Agent")

# Retrieve the saved profile from the agent's memory on startup
profile = st.session_state.agent.memory.get_profile()

# Use stored profile values instead of hardcoded defaults
st.sidebar.header("Agent Constraints")
country = st.sidebar.text_input(
    "Country (for localized pricing)", 
    value=profile.get("country", "New Zealand")
)
currency = st.sidebar.text_input(
    "Currency Symbol", 
    value=profile.get("currency", "NZD")
)
budget_limit = st.sidebar.number_input(
    "Maximum Budget", 
    min_value=1.0, 
    value=float(profile.get("budget_limit") or 60.0), 
    step=1.0
)
days = st.sidebar.slider(
    "Duration (Days)", 
    min_value=1, 
    max_value=7, 
    value=profile.get("days", 3)
)

# Handle dietary defaults
diet_options = ["Vegetarian", "Vegan", "Gluten-Free"]
saved_diets = [d for d in profile.get("dietary_restrictions", []) if d in diet_options]
selected_diet = st.sidebar.multiselect(
    "Dietary Requirements", 
    diet_options, 
    default=saved_diets
)

# Handle allergy defaults
saved_allergies = ", ".join(profile.get("allergies", []))
allergies_input = st.sidebar.text_input(
    "Allergies (comma-separated)", 
    value=saved_allergies
)
allergies_list = [a.strip() for a in allergies_input.split(",") if a.strip()]


# Active constraint package
constraints = {
    "country": country,
    "currency": currency,
    "budget_limit": budget_limit if budget_limit > 0 else None,
    "days": days,
    "dietary_restrictions": selected_diet,
    "allergies": allergies_list,
    "current_plan": st.session_state.current_plan
}

if st.sidebar.button("Generate Without Prompt"):
    st.session_state.messages.append({"role": "user", "content": "Please generate a new plan based on the current constraints."})
    st.rerun()

if st.sidebar.button("Save Constraints to Profile"):
    constraints_to_save = constraints.copy()
    constraints_to_save.pop("current_plan", None)
    st.session_state.agent.memory.save_profile(constraints_to_save)
    st.sidebar.success("Constraints saved successfully!")

# Responsive Column Layout
chat_col, plan_col = st.columns([1, 1])

with chat_col:
    st.subheader("Chat Assistant")
    
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    if user_prompt := st.chat_input("Ask me to generate a plan, modify something..."):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        st.session_state.current_plan = st.session_state.current_plan # Keep plan state
        st.rerun()

    # Run the agent processing step after the page rerun so UI updates sequentially
    if st.session_state.messages[-1]["role"] == "user":
        user_prompt = st.session_state.messages[-1]["content"]
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Processing request..."):
                    response_text, updated_plan = st.session_state.agent.process_input(user_prompt, constraints)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    if updated_plan:
                        st.session_state.current_plan = updated_plan
                    st.rerun()

with plan_col:
    st.subheader("Active Meal Plan Output")
    
    # By wrapping the output inside a container with a fixed height (e.g., 720 pixels),
    # Streamlit adds an independent vertical scrollbar to only this section.
    with st.container(height=520):
        if st.session_state.current_plan:
            plan = st.session_state.current_plan

            # 1. Cost & Export Action Area
            cost_col, btn_col = st.columns([1, 1])
            with cost_col:
                cost = plan.get("estimated_total_cost", 0)
                st.metric(label=f"Estimated Total Cost ({currency})", value=f"{currency} {cost:.2f}")
            
            with btn_col:
                # Format plan data into markdown
                plan_md = format_plan_to_markdown(plan, currency)
                
                # Render Streamlit's native download button
                st.write(" ")  # Spacer to align vertically with metric
                st.write(" ")
                st.download_button(
                    label="📥 Export Plan & Groceries",
                    data=plan_md,
                    file_name="meal_plan_and_groceries.md",
                    mime="text/markdown"
                )

            st.markdown("### 📅 Meals")
            for day, meals in plan.get("meals", {}).items():
                with st.expander(f"**{day}**", expanded=True):
                    for meal_type, meal_info in meals.items():
                        meal_name = meal_info.get("name", "")
                        st.write(f"**{meal_type}:** {meal_name}")
                        
                        with st.expander("View Recipe"):
                            recipe = st.session_state.agent.get_recipe(meal_name)
                            recipe_md = format_recipe_to_markdown(recipe)
                            st.info(recipe_md)  # Display recipe details in an info box
                            st.download_button(
                                key=f"download_{meal_name}_day_{day}",
                                label="📥 Export Recipe",
                                data=recipe_md,
                                file_name=f"{recipe.get('name', '')}_recipe.md",
                                mime="text/markdown"
                            )


            st.markdown("### 🛒 Shopping Checklist")
            grocery_list = plan.get("grocery_list", [])
            if grocery_list:
                for item in grocery_list:
                    item_name = item.get("item", "")
                    item_price = item.get("estimated_price", 0.0)
                    st.write(f"- [ ] {item_name} (~ {currency} {item_price:.2f})")
            else:
                st.write("No ingredients listed.")
        else:
            st.info("No plan generated yet. Send a message to the agent to get started.")