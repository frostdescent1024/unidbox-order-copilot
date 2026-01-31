# API Module for UnidBox Order Copilot
# This module provides REST API endpoints for the frontend

from .routes import create_app, api_router

__all__ = ['create_app', 'api_router']
