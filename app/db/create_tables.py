import os
import sys

# Add the parent directory to sys.path to allow imports from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.database import engine, Base
from app.db.models import *

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")
