import os

DATA_DIR = os.getenv("ORGANISMO_DATA_DIR", os.path.join(os.getenv("DATA_DIR", "./data"), "organismo"))
