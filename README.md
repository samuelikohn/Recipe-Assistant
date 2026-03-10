# Recipe Assistant

A Streamlit-based recipe app powered by OpenAI. Chat with an AI assistant to discover, create, and refine recipes. Save your favorites to browser localStorage and edit them anytime.

## Features

- **AI Chat** — Conversational recipe creation and Q&A using OpenAI (GPT-5.4) with function calling
- **Spoonacular Integration** — Search real recipes, find recipes by ingredients, get nutritional info, and more via the [Spoonacular API](https://spoonacular.com/food-api)
- **Structured Recipe Output** — The AI uses a dedicated `save_recipe` tool to present recipes as formatted cards with ingredients, instructions, and metadata
- **Save & Edit** — Save recipes to browser localStorage. View, edit, or delete them from the sidebar
- **Persistent Storage** — Recipes survive page refreshes (stored in browser localStorage)

## Project Structure

```
app.py              — Main Streamlit app (chat UI, sidebar, recipe viewer/editor)
llm.py              — OpenAI client, tool definitions, tool dispatch loop
spoonacular.py      — Spoonacular REST API wrapper (6 endpoints)
recipes.py          — Recipe data model and CRUD operations
local_storage.py    — Browser localStorage bridge via streamlit-js
requirements.txt    — Python dependencies
.env.example        — API key template
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

Copy the example env file and add your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=your_openai_api_key
SPOONACULAR_API_KEY=your_spoonacular_api_key
```

- **OpenAI API key**: Get one at [platform.openai.com](https://platform.openai.com/api-keys)
- **Spoonacular API key** (free tier: 150 requests/day): Get one at [spoonacular.com/food-api/console](https://spoonacular.com/food-api/console#Dashboard)

### 3. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Usage

1. **Ask for a recipe** — Type something like "Give me a quick pasta recipe" in the chat box
2. **Search with Spoonacular** — Ask "Search for vegan desserts" or "What can I make with chicken and rice?"
3. **Save a recipe** — Click the "Save to My Recipes" button on any recipe card
4. **View/edit saved recipes** — Click a recipe title in the sidebar to view it, then click "Edit Recipe" to modify
5. **Get nutritional info** — Ask "What's the nutrition for 2 cups rice, 1 chicken breast?"

## AI Tools

The assistant has access to 7 tools:

| Tool | Description |
|------|-------------|
| `search_recipes` | Search Spoonacular by query, diet, cuisine, ingredients |
| `get_recipe_information` | Get full details for a Spoonacular recipe by ID |
| `search_ingredients` | Look up ingredient information |
| `find_recipes_by_ingredients` | Find recipes matching ingredients you have |
| `get_random_recipes` | Get random recipe suggestions with optional filters |
| `analyze_nutrition` | Nutritional analysis for a list of ingredients |
| `save_recipe` | Present a structured recipe card to the user |

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI framework
- [OpenAI API](https://platform.openai.com/) — LLM with function calling
- [Spoonacular API](https://spoonacular.com/food-api) — Recipe and nutrition data
- [streamlit-js](https://github.com/nickolay-sheyko/streamlit_js) — Browser JS execution for localStorage
