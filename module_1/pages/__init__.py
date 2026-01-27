from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__, template_folder='../templates')

@pages_bp.route('/')
def home():
    return render_template('home.html')

@pages_bp.route('/contact')
def contact():
    return render_template('contact.html')

@pages_bp.route('/projects')
def projects():
    return render_template('projects.html')

@pages_bp.route('/references')
def references():
    return render_template('references.html')