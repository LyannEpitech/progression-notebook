"""
Dashboard Pool Progression – Epitech
DEPRECATED: Ce fichier est conservé pour compatibilité Docker.
La nouvelle architecture est dans src/ui/app.py
"""

import warnings
warnings.warn(
    "dashboard.py is deprecated. Use src.ui.app:main instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import et exécution de la nouvelle application
from src.ui.app_main import main

if __name__ == "__main__":
    main()
