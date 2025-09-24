# app.py
from flask import Flask, jsonify
from sqlalchemy import text
from dotenv import load_dotenv
import os

# Import db and JWT
from extensions import db
from flask_jwt_extended import JWTManager

from routes import bp as api_bp



load_dotenv()

# ------------------------
# Initialize Flask app
# ------------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")

# Register the Blueprint
app.register_blueprint(api_bp)

# ------------------------
# Initialize extensions
# ------------------------
db.init_app(app)
jwt = JWTManager(app)

# ------------------------
# Simple healthcheck route
# ------------------------
@app.route("/")
def home():
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return jsonify({
                    "status": "CrewQuick API running!",
                    "db_connection": "✅ successful"
                })
            else:
                return jsonify({
                    "status": "CrewQuick API running!",
                    "db_connection": "❌ failed"
                })
    except Exception as e:
        return jsonify({
            "status": "CrewQuick API running!",
            "db_connection": "❌ failed",
            "error": str(e)
        })

# ------------------------
# Import routes AFTER db & app are initialized
# ------------------------
import routes  # contains signup/login endpoints

# ------------------------
# Run app
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)
