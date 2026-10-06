# -*- coding: utf-8 -*-
"""
Routes package for LXP Sale Monitor.
Initializes and registers all modular Flask Blueprints.
"""

from .auth import auth_bp
from .dashboard import dashboard_bp
from .morning_audit import morning_audit_bp
from .daily_report import daily_report_bp
from .inspection import inspection_bp
from .admin import admin_bp
from .maid import maid_bp

def register_blueprints(app):
    """Registers all application blueprints to the Flask app instance."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(morning_audit_bp)
    app.register_blueprint(daily_report_bp)
    app.register_blueprint(inspection_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(maid_bp)
