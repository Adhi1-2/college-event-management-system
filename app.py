from flask import Flask
from config import Config
from extensions import mysql, mail

# ✅ Create App
app = Flask(__name__)

# ✅ Load Config
app.config.from_object(Config)

# ✅ Initialize Extensions
mysql.init_app(app)
mail.init_app(app)

# ✅ Register Blueprint
from auth import auth
app.register_blueprint(auth)

# ✅ Run Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
