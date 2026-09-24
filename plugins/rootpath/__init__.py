from . import models  # noqa: F401  (registra los modelos en db)

def load(app):
    from .api import bp
    app.register_blueprint(bp)
