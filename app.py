import os

import streamlit as st

try:
    for key, value in st.secrets.items():
        os.environ.setdefault(key, str(value))
except Exception:
    pass

if "DATABASE_URL" not in os.environ:
    st.warning("DATABASE_URL not set -- falling back to local SQLite.")

from ui.app import main


if __name__ == "__main__":
    main()
