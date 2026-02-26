"""Point d'entrée principal de l'application Streamlit."""

import os
import sys
import streamlit as st

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.ui.app_main import main

if __name__ == "__main__":
    main()
