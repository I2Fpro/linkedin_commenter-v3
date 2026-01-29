"""
Version management - lit depuis env var APP_VERSION.
Definie au build Docker via --build-arg APP_VERSION=X.Y.Z.HHMM
"""
import os

VERSION = os.getenv("APP_VERSION", "0.0.0-unknown")
