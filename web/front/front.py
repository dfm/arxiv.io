__all__ = ["bp"]


import flask


bp = flask.Blueprint("front", __name__,
                     static_folder="static",
                     template_folder="templates")


@bp.route("/")
def index():
    return flask.render_template("index.html")
