from flask import Blueprint, render_template

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403