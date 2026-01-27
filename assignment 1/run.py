from flask import Flask, render_template
from pages import pages_bp

app = Flask(__name__)

# Register blueprint
app.register_blueprint(pages_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)