from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/robvoigt/robvoigt/static/test.db'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 # max upload filesize 1MB

db = SQLAlchemy(app)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


if __name__ == "__main__":
    app.run()

import robvoigt.views
