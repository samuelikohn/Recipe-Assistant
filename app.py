import streamlit as st
from dotenv import load_dotenv
import os
import json
from local_storage import StLocalStorage
import llm
import recipes as rec


load_dotenv()

st.set_page_config(page_title="Recipe Assistant", page_icon="🍳", layout="wide")

local_storage = StLocalStorage()

# Load recipes from localStorage once per render
rec.init_recipes(local_storage)

# --- Session state init ---
if "messages" not in st.session_state:
    st.session_state.messages = []  # OpenAI message dicts
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []  # {role, content, recipes?}
if "viewing_recipe" not in st.session_state:
    st.session_state.viewing_recipe = None
if "editing" not in st.session_state:
    st.session_state.editing = False


# --- API key setup ---
def get_api_keys():
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    spoonacular_key = os.environ.get("SPOONACULAR_API_KEY", "")
    return openai_key, spoonacular_key


openai_key, spoonacular_key = get_api_keys()

# --- Sidebar ---
with st.sidebar:
    st.header("My Recipes")

    saved = rec.get_recipes()

    if not saved:
        st.caption("No saved recipes yet. Chat to create one!")

    for recipe in saved:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"📖 {recipe.title}", key=f"view_{recipe.id}", use_container_width=True):
                st.session_state.viewing_recipe = recipe.id
                st.session_state.editing = False
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{recipe.id}"):
                rec.delete_recipe(local_storage, recipe.id)
                if st.session_state.viewing_recipe == recipe.id:
                    st.session_state.viewing_recipe = None
                st.rerun()

    st.divider()
    if st.button("Back to Chat", use_container_width=True):
        st.session_state.viewing_recipe = None
        st.session_state.editing = False
        st.rerun()


# --- Recipe card rendering ---
def render_recipe_card(recipe_data, allow_save=True):
    """Render a recipe as a nice card. recipe_data is a dict."""
    title = recipe_data.get("title", "Untitled Recipe")
    ingredients = recipe_data.get("ingredients", [])
    instructions = recipe_data.get("instructions", [])
    servings = recipe_data.get("servings", "")
    prep_time = recipe_data.get("prep_time", "")
    cuisine = recipe_data.get("cuisine", "")
    notes = recipe_data.get("notes", "")

    with st.container(border=True):
        st.subheader(title)

        meta_parts = []
        if servings:
            meta_parts.append(f"Servings: {servings}")
        if prep_time:
            meta_parts.append(f"Time: {prep_time}")
        if cuisine:
            meta_parts.append(f"Cuisine: {cuisine}")
        if meta_parts:
            st.caption(" | ".join(meta_parts))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Ingredients:**")
            for ing in ingredients:
                st.markdown(f"- {ing}")
        with col2:
            st.markdown("**Instructions:**")
            for i, step in enumerate(instructions, 1):
                st.markdown(f"{i}. {step}")

        if notes:
            st.info(f"💡 {notes}")

        if allow_save:
            key = f"save_{title}_{hash(json.dumps(recipe_data, sort_keys=True))}"
            if st.button("💾 Save to My Recipes", key=key):
                recipe = rec.Recipe(
                    title=title,
                    ingredients=ingredients,
                    instructions=instructions,
                    servings=servings if servings else 4,
                    prep_time=prep_time,
                    cuisine=cuisine,
                    notes=notes,
                )
                rec.add_recipe(local_storage, recipe)
                st.success(f"Saved '{title}'!")
                st.rerun()


# --- Recipe view/edit mode ---
def render_recipe_viewer():
    saved = rec.get_recipes()
    recipe = next((r for r in saved if r.id == st.session_state.viewing_recipe), None)

    if not recipe:
        st.warning("Recipe not found.")
        st.session_state.viewing_recipe = None
        return

    if st.session_state.editing:
        st.header(f"Editing: {recipe.title}")

        new_title = st.text_input("Title", value=recipe.title)
        new_servings = st.number_input("Servings", value=recipe.servings, min_value=1)
        new_prep_time = st.text_input("Prep Time", value=recipe.prep_time)
        new_cuisine = st.text_input("Cuisine", value=recipe.cuisine)
        new_ingredients = st.text_area(
            "Ingredients (one per line)", value="\n".join(recipe.ingredients)
        )
        new_instructions = st.text_area(
            "Instructions (one per line)", value="\n".join(recipe.instructions)
        )
        new_notes = st.text_area("Notes", value=recipe.notes)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Changes", type="primary", use_container_width=True):
                recipe.title = new_title
                recipe.servings = new_servings
                recipe.prep_time = new_prep_time
                recipe.cuisine = new_cuisine
                recipe.ingredients = [i.strip() for i in new_ingredients.split("\n") if i.strip()]
                recipe.instructions = [i.strip() for i in new_instructions.split("\n") if i.strip()]
                recipe.notes = new_notes
                rec.update_recipe(local_storage, recipe)
                st.session_state.editing = False
                st.success("Recipe updated!")
                st.rerun()
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.editing = False
                st.rerun()
    else:
        render_recipe_card(recipe.to_dict(), allow_save=False)
        if st.button("✏️ Edit Recipe"):
            st.session_state.editing = True
            st.rerun()


# --- Main area ---
if st.session_state.viewing_recipe:
    render_recipe_viewer()
else:
    st.title("🍳 Recipe Assistant")
    st.caption("Ask me to find, create, or improve recipes!")

    # Display chat history
    for msg in st.session_state.display_messages:
        with st.chat_message(msg["role"]):
            if msg.get("content"):
                st.markdown(msg["content"])
            if msg.get("recipes"):
                for r in msg["recipes"]:
                    render_recipe_card(r)

    # Chat input
    if prompt := st.chat_input("What would you like to cook?"):
        if not openai_key:
            st.error("Please set your OPENAI_API_KEY in the .env file.")
            st.stop()

        # Show user message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.display_messages.append({"role": "user", "content": prompt})

        # Add to OpenAI history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Call LLM
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    client = llm.create_client(openai_key)
                    response_text, response_recipes = llm.chat(
                        client, st.session_state.messages
                    )

                    if response_text:
                        st.markdown(response_text)
                    for r in response_recipes:
                        render_recipe_card(r)

                    st.session_state.display_messages.append(
                        {
                            "role": "assistant",
                            "content": response_text,
                            "recipes": response_recipes,
                        }
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
