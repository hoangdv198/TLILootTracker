"""
UI Components Package
=====================

This package contains UI components:
- ui: Main application window and UI components
"""
# Chỉ import App, không import ui module để tránh circular import và duplicate
from .ui import App

__all__ = ['App']

