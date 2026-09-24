# -*- coding: utf-8 -*-
"""Flag dinamica por usuario para los retos de servicio de RootPath.

- user_flag(user_id, challenge_id, slug): valor esperado para ese usuario.
- Se registra el tipo "rootpath" en CTFd para validar el intento.
El contenedor recibe el mismo valor por la variable de entorno RP_FLAG.
"""
import hashlib

from CTFd.plugins.flags import FLAG_CLASSES
from CTFd.utils.user import get_current_user


def _secret():
    try:
        with open("/opt/CTFd/runtime/flag_secret", encoding="utf-8") as fh:
            return fh.read().strip()
    except Exception:
        return "rootpath-default-flag-secret"


def user_flag(user_id, challenge_id, slug):
    slug = (slug or "rootpath").strip()
    raw = "%s:%s:%s" % (_secret(), user_id, challenge_id)
    h = hashlib.sha256(raw.encode()).hexdigest()[:8]
    return "RP{%s_%s}" % (slug, h)


class RootPathDynamicFlag(object):
    name = "rootpath"
    templates = {}

    @staticmethod
    def compare(chal_key_obj, provided):
        user = get_current_user()
        if not user:
            return False
        expected = user_flag(user.id, chal_key_obj.challenge_id, chal_key_obj.content or "")
        return provided == expected


def register():
    FLAG_CLASSES["rootpath"] = RootPathDynamicFlag
