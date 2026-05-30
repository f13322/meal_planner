# Meal Planning Agent Prototype

This is a prototype of an intelligent, personal task-planning software agent built using Python, Streamlit, and the modern `google-genai` SDK. It processes conversational inputs to generate, modify, and export custom meal plans while validating budget, allergy, and dietary constraints locally. Since this is a prototype, data such as user preference, and recipes will be stored in a local json file instead of a database. Due to thsi, the first few runs will take a lot longer due to the need to populate the recipe catalogue, but should improve for prolonged use.

https://github.com/user-attachments/assets/f7810658-cbb8-4f72-95ff-1c139f8955e6

## Directory Structure

Ensure the following files exists:

```text
meal-planner/
│
├── app.py              # Streamlit frontend (Chat and Active Plan split layout)
├── agent.py            # Agent Orchestrator (Coordinates view, planning, and validation)
├── planner.py          # LLM Integration (Handles prompting, JSON outputs, and retry logic)
├── validator.py        # Programmatic Validation (Deterministic constraint checker)
├── memory.py           # State & Persistence Manager (Reads/writes JSON state files)
├── recipes.json        # Local recipe database (Initial seed files and cached outputs)
├── memory.json         # User Profile data and current plan state
├── rules.json          # Programmatic rules for vegetarian, vegan, and gluten-free filters
├── helpers.py          # Helper functions for formatting exported files
├── requirements.txt    # Python dependencies
├── README.md		# Set up insteructions
└── .env                # API Keys (Not commited to the repository)
```

## Prerequisites

- **Minimum Python Version:** $\ge$ 3.10
- **Recommended Python Version:** 3.12.9
- **Gemini API Key:** A valid Google Gemini API Key

## Setup

**1. Configure Environment Variables**\n

Create a `.env` file in the project root and add your Gemini API Key and the model:

    GEMINI_API_KEY=your_gemini_api_key
    AGENT_MODEL=model_for_your_agent (gemini-2.5-pro recommended)

**2. Set Up a Virtual Environment (Recommended)**

Creating a virtual environment ensures dependencies do not conflict with other system packages.

    # Create the environment
    python -m venv venv

    # Activate the environment (macOS/Linux)
    source venv/bin/activate

    # Activate the environment (Windows)
    venv\Scripts\activate

**3. Instal Dependencies**

    pip install -r requirements.txt

## Running the app

Start the Streamlit web servery by running the following command

    streamlit run app.py

## Evaluation and Limitations

The aget is capable of producing realistic meal plans that stays within the constraints, it can identify when the conditions such as the budget is too restrictive to provide reasoning and example plans with feasible constraints. Currently, the agent is quite slow due to multiple reasons. The agent does not run asynchronously, where
