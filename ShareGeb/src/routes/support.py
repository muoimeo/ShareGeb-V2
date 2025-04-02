from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from src.models import db, User

support_bp = Blueprint('support', __name__)

@support_bp.route('/support', methods=['GET'])
def support():
    return render_template('support/support.html') 