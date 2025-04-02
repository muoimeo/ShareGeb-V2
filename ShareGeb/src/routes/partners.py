from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from src.models import db, User

partners_bp = Blueprint('partners', __name__)

@partners_bp.route('/become-partner', methods=['GET'])
def become_partner():
    return render_template('partners/become_partner.html') 