__all__ = ['app']

import flask
from flask_sslify import SSLify

import config
import front

# Set up the flask application.
app = flask.Flask(__name__)
SSLify(app, subdomains=True)
app.config.from_object(config)


# reader.oid.init_app(app)
# reader.login_manager.setup_app(app)


# Register the blueprints.
if app.config["TESTING"]:
    app.register_blueprint(front.bp, url_prefix="/arxiv")
else:
    app.register_blueprint(front.bp, subdomain="www")


# Run in development mode.
if __name__ == "__main__":
    app.run(host="localhost", port=8000)
