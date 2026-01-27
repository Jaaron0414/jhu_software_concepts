# Import Flask for web framework and render_template for rendering HTML templates
from flask import Flask, render_template
# Import the blueprint from the pages module
from pages import pages_bp

# Create a Flask application instance
app = Flask(__name__)

# Register the blueprint to the app, allowing routes defined in pages to be used
app.register_blueprint(pages_bp)

# Run the app if this script is executed directly
if __name__ == '__main__':
    # Start the Flask development server on all interfaces (0.0.0.0) at port 8080 with debug mode enabled
    app.run(host='0.0.0.0', port=8080, debug=True)