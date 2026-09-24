from . import models  # noqa: F401


def load(app):
    from .api import bp
    app.register_blueprint(bp)
    try:
        from CTFd.utils.plugins import register_plugin_script
        register_plugin_script("/plugins/rootpath/static/nav.js")
    except Exception:
        pass
