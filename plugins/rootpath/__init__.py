from . import models  # noqa: F401


def load(app):
    from .api import bp
    app.register_blueprint(bp)
    try:
        from CTFd.plugins import register_plugin_script, register_plugin_stylesheet
        register_plugin_stylesheet("/plugins/rootpath/static/hide-menu.css")
        register_plugin_script("/plugins/rootpath/static/nav.js")
    except Exception as e:
        app.logger.warning("rootpath plugin assets: %s" % e)
