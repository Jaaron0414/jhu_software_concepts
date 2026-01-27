# Import Blueprint for organizing routes and render_template for rendering templates
from flask import Blueprint, render_template

# Create a blueprint named 'pages' with template folder relative to this module
pages_bp = Blueprint('pages', __name__, template_folder='../templates')

# Define route for home page
@pages_bp.route('/')
def home():
    # Render the home.html template
    return render_template('home.html')

# Define route for contact page
@pages_bp.route('/contact')
def contact():
    # Render the contact.html template
    return render_template('contact.html')

# Define route for projects page
@pages_bp.route('/projects')
def projects():
    # Render the projects.html template
    return render_template('projects.html')

# Define route for references page
@pages_bp.route('/references')
def references():
    # Render the references.html template
    return render_template('references.html')