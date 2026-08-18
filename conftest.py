import os
import sys

# app.py vive dentro de la carpeta app/, no en la raíz del repo.
# Agregamos esa carpeta al path para poder hacer `from app import app`.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
