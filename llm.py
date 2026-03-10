import json
from openai import OpenAI
import spoonacular

MODEL = "gpt-5.4"

SYSTEM_INSTRUCTION = """You are a helpful recipe assistant. You help users discover, create, and refine recipes.

When the user asks for a recipe or you want to present a recipe, ALWAYS use the save_recipe tool to output it in structured format. Do not just write recipe text — call the tool so the user can save it.

When the user asks to search for recipes, look up ingredients, or get nutritional info, use the appropriate Spoonacular tools.

Be friendly, knowledgeable about cooking, and proactive about suggesting improvements or variations."""

# --- Tool definitions (OpenAI function calling format) ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_recipes",
            "description": "Search for recipes based on ingredients, diet, cuisine, and other criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query for recipes"},
                    "number": {"type": "integer", "description": "Number of results (1-10)", "default": 5},
                    "diet": {"type": "string", "description": "Diet type (vegetarian, vegan, gluten-free, etc.)"},
                    "cuisine": {"type": "string", "description": "Cuisine type (italian, mexican, chinese, etc.)"},
                    "include_ingredients": {"type": "string", "description": "Comma-separated ingredients to include"},
                    "exclude_ingredients": {"type": "string", "description": "Comma-separated ingredients to exclude"},
                    "meal_type": {"type": "string", "description": "Meal type (main course, side dish, dessert, etc.)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recipe_information",
            "description": "Get detailed information about a specific recipe by its Spoonacular ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_id": {"type": "integer", "description": "The Spoonacular recipe ID"},
                    "include_nutrition": {"type": "boolean", "description": "Include nutrition info", "default": False},
                },
                "required": ["recipe_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_ingredients",
            "description": "Search for ingredients by name to get information about them",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The ingredient search query"},
                    "number": {"type": "integer", "description": "Number of results", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_recipes_by_ingredients",
            "description": "Find recipes that can be made with the ingredients the user has",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredients": {"type": "string", "description": "Comma-separated list of ingredients"},
                    "number": {"type": "integer", "description": "Number of recipes to find", "default": 5},
                },
                "required": ["ingredients"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_random_recipes",
            "description": "Get random recipe suggestions, optionally filtered by tags",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "integer", "description": "Number of random recipes", "default": 1},
                    "tags": {"type": "string", "description": "Comma-separated tags (diet, meal type, etc.)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_nutrition",
            "description": "Analyze nutrition information for a list of ingredients",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredient_list": {"type": "string", "description": "Ingredients, one per line"},
                    "servings": {"type": "integer", "description": "Number of servings", "default": 1},
                },
                "required": ["ingredient_list"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_recipe",
            "description": "Present a recipe to the user in structured format so they can review and save it. ALWAYS use this tool when creating or presenting a recipe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Recipe title"},
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ingredients with quantities",
                    },
                    "instructions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Step-by-step cooking instructions",
                    },
                    "servings": {"type": "integer", "description": "Number of servings"},
                    "prep_time": {"type": "string", "description": "Preparation/cooking time (e.g. '30 minutes')"},
                    "cuisine": {"type": "string", "description": "Cuisine type"},
                    "notes": {"type": "string", "description": "Additional tips or notes"},
                },
                "required": ["title", "ingredients", "instructions"],
            },
        },
    },
]


def _dispatch_tool(name, args):
    """Execute a tool call and return the result."""
    if name == "save_recipe":
        return {"status": "recipe_presented", "recipe": args}

    func_map = {
        "search_recipes": spoonacular.search_recipes,
        "get_recipe_information": spoonacular.get_recipe_information,
        "search_ingredients": spoonacular.search_ingredients,
        "find_recipes_by_ingredients": spoonacular.find_recipes_by_ingredients,
        "get_random_recipes": spoonacular.get_random_recipes,
        "analyze_nutrition": spoonacular.analyze_nutrition,
    }

    func = func_map.get(name)
    if not func:
        return {"error": f"Unknown tool: {name}"}

    try:
        result = func(**args)
        return result
    except Exception as e:
        return {"error": str(e)}


def create_client(api_key):
    return OpenAI(api_key=api_key)


def chat(client, messages):
    """
    Send messages to OpenAI with tools, handle tool calls, return final response.

    Args:
        client: OpenAI client instance
        messages: list of message dicts (OpenAI chat format)

    Returns:
        (response_text, list_of_recipes) — recipes are from save_recipe calls
    """
    recipes = []

    # Ensure system message is first
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": SYSTEM_INSTRUCTION})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
    )

    message = response.choices[0].message

    # Tool call loop
    max_iterations = 10
    iteration = 0
    while message.tool_calls and iteration < max_iterations:
        iteration += 1

        # Append assistant message with tool calls
        messages.append(message.model_dump(exclude_none=True))

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = _dispatch_tool(tool_call.function.name, args)

            if tool_call.function.name == "save_recipe" and "recipe" in result:
                recipes.append(result["recipe"])

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message

    # Extract final text
    text = message.content or ""

    # Append final assistant message to history
    messages.append({"role": "assistant", "content": text})

    return text, recipes
