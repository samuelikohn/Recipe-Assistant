import json
from typing import Any
import uuid
import streamlit as st
from streamlit_js import st_js, st_js_blocking


KEY_PREFIX = "st_localstorage_"


class StLocalStorage:

    def __init__(self):
        # Keep track of a UUID for each key to enable reruns
        if "_ls_unique_keys" not in st.session_state:
            st.session_state["_ls_unique_keys"] = {}

    def __getitem__(self, key: str) -> Any:
        if key not in st.session_state["_ls_unique_keys"]:
            st.session_state["_ls_unique_keys"][key] = str(uuid.uuid4())
        code = f"return localStorage.getItem('{KEY_PREFIX + key}');"
        result = st_js(code)
        if result and result[0]:
            return json.loads(result[0])
        return None

    def __setitem__(self, key: str, value: Any) -> None:
        value = json.dumps(value, ensure_ascii=False)
        st.session_state["_ls_unique_keys"][key] = str(uuid.uuid4())
        code = f"localStorage.setItem('{KEY_PREFIX + key}', {value});"
        return st_js(code, key=st.session_state["_ls_unique_keys"][key] + "_set")

    def get_blocking(self, key: str) -> Any:
        code = f"return localStorage.getItem('{KEY_PREFIX + key}');"
        result = st_js_blocking(code, key=f"_ls_blocking_{key}")
        if result:
            return json.loads(result)
        return None