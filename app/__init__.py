from flask import Flask

from .db import close_db, init_app


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=app.instance_path + "/benchflow.sqlite",
    )

    # Register DB teardown before any startup app context opens a connection.
    # Otherwise init_db() can leak one connection per app instance.
    app.teardown_appcontext(close_db)
    init_app(app)

    from .routes import bp

    app.register_blueprint(bp)

    return app
