# sitecustomize.py - executed VERY early in Python startup
# This is loaded from site-packages automatically
import os

os.environ["RAGFLOW_TESTING"] = "1"
