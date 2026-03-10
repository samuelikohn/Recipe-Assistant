import os
import requests

API_BASE = "https://api.spoonacular.com"


def _get_api_key():
    key = os.environ.get("SPOONACULAR_API_KEY", "")
    if not key:
        raise ValueError("SPOONACULAR_API_KEY environment variable is required")
    return key


def _get(endpoint, params=None):
    params = params or {}
    params["apiKey"] = _get_api_key()
    resp = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _post(endpoint, data=None, params=None):
    params = params or {}
    params["apiKey"] = _get_api_key()
    resp = requests.post(
        f"{API_BASE}{endpoint}",
        data=data,
        params=params,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def search_recipes(
    query,
    number=10,
    diet=None,
    intolerances=None,
    include_ingredients=None,
    exclude_ingredients=None,
    meal_type=None,
    cuisine=None,
):
    params = {"query": query, "number": number}
    if diet:
        params["diet"] = diet
    if intolerances:
        params["intolerances"] = intolerances
    if include_ingredients:
        params["includeIngredients"] = include_ingredients
    if exclude_ingredients:
        params["excludeIngredients"] = exclude_ingredients
    if meal_type:
        params["type"] = meal_type
    if cuisine:
        params["cuisine"] = cuisine
    return _get("/recipes/complexSearch", params)


def get_recipe_information(recipe_id, include_nutrition=False):
    return _get(
        f"/recipes/{recipe_id}/information",
        {"includeNutrition": str(include_nutrition).lower()},
    )


def search_ingredients(query, number=10, meta_information=False):
    return _get(
        "/food/ingredients/search",
        {
            "query": query,
            "number": number,
            "metaInformation": str(meta_information).lower(),
        },
    )


def analyze_nutrition(ingredient_list, servings):
    return _post(
        "/recipes/parseIngredients",
        data={"ingredientList": ingredient_list, "servings": str(servings)},
    )


def find_recipes_by_ingredients(ingredients, number=5, ranking=1):
    return _get(
        "/recipes/findByIngredients",
        {"ingredients": ingredients, "number": number, "ranking": ranking},
    )


def get_random_recipes(number=1, tags=None):
    params = {"number": number}
    if tags:
        params["tags"] = tags
    return _get("/recipes/random", params)
