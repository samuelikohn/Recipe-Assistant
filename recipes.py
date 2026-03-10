from dataclasses import dataclass, field, asdict
import json
import uuid
import streamlit as st

@dataclass
class Recipe:
    title: str
    ingredients: list[str]
    instructions: list[str]
    servings: int = 4
    prep_time: str = ""
    cuisine: str = ""
    image_url: str = ""
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


STORAGE_KEY = "saved_recipes"


def _parse_raw(raw) -> list[Recipe]:
    if not raw:
        return []
    try:
        if isinstance(raw, str):
            raw = json.loads(raw)
        return [Recipe.from_dict(r) for r in raw]
    except (json.JSONDecodeError, TypeError, AttributeError):
        return []


def init_recipes(local_storage):
    if "_recipes_cache" not in st.session_state:
        raw = local_storage.get_blocking(STORAGE_KEY)
        st.session_state["_recipes_cache"] = _parse_raw(raw)


def get_recipes() -> list[Recipe]:
    return list(st.session_state.get("_recipes_cache", []))


def save_recipes(local_storage, recipes: list[Recipe]):
    st.session_state["_recipes_cache"] = recipes
    local_storage[STORAGE_KEY] = [r.to_dict() for r in recipes]


def add_recipe(local_storage, recipe: Recipe):
    recipes = get_recipes()
    recipes.append(recipe)
    save_recipes(local_storage, recipes)


def update_recipe(local_storage, recipe: Recipe):
    recipes = get_recipes()
    recipes = [recipe if r.id == recipe.id else r for r in recipes]
    save_recipes(local_storage, recipes)


def delete_recipe(local_storage, recipe_id: str):
    recipes = get_recipes()
    recipes = [r for r in recipes if r.id != recipe_id]
    save_recipes(local_storage, recipes)
