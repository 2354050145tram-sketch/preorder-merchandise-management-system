"""Thiết lập môi trường test trước khi pytest import application."""

import os


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("FLASK_SECRET_KEY", "unit-test-secret")
