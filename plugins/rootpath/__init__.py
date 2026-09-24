from . import models  # noqa: F401


def load(app):
    # Garantiza que existan las tablas del plugin (idempotente: solo crea las que faltan).
    try:
        with app.app_context():
            app.db.create_all()
    except Exception as e:
        app.logger.warning("rootpath db.create_all: %s" % e)

    from .api import bp
    app.register_blueprint(bp)

    # Tipo de flag dinamica por usuario (retos de servicio).
    try:
        from . import flags as _rp_flags
        _rp_flags.register()
    except Exception as e:
        app.logger.warning("rootpath flags: %s" % e)
    try:
        from CTFd.plugins import register_plugin_script, register_plugin_stylesheet
        register_plugin_stylesheet("/plugins/rootpath/static/hide-menu.css")
        register_plugin_script("/plugins/rootpath/static/nav.js")
    except Exception as e:
        app.logger.warning("rootpath plugin assets: %s" % e)

    # Landing de bienvenida: login/registro de CTFd renderizados con la UI RootPath.
    try:
        import os
        from CTFd.plugins import override_template
        from CTFd.models import UserFields
        tpl = os.path.join(os.path.dirname(__file__), "templates", "welcome.html")
        with open(tpl, encoding="utf-8") as fh:
            base = fh.read()
        with app.app_context():
            f = UserFields.query.filter_by(name="Nombre completo").first()
            fid = str(f.id) if f else ""

        def _variant(tab):
            h = base.replace("{{ default_tab|default('login') }}", tab)
            h = h.replace("{{ fullname_field_id or '' }}", fid)
            return h

        override_template("login.html", _variant("login"))
        override_template("register.html", _variant("register"))
    except Exception as e:
        app.logger.warning("rootpath welcome override: %s" % e)
