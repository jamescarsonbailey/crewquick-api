from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from models import User, Worker, Contractor, Job, JobApplication
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route("/")
def home():
    try:
        # SQLAlchemy 2.x requires text() for raw SQL
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

if __name__ == "__main__":
    app.run(debug=True)
