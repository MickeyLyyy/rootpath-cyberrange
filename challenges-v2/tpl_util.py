# -*- coding: utf-8 -*-
"""Utilidades y generación de documentos compartidos por todos los builders."""
import re, secrets

DIFF_NAME = {1: "Facil", 2: "Media", 3: "Dificil"}
PTS = {1: 50, 2: 100, 3: 200}


def gen_flag(slug):
    return "RP{%s_%s}" % (re.sub(r"[^a-z0-9]", "_", slug)[:24], secrets.token_hex(3))


def render_docs(spec, flag, meta, solve_note):
    d = DIFF_NAME[spec["difficulty"]]
    pts = PTS[spec["difficulty"]]
    kind = "container" if meta["kind"] == "service" else "static"
    conn = meta.get("connection", "Ver artefacto adjunto.")

    yml = "\n".join([
        "id: %s" % spec["slug"],
        "title: \"%s\"" % spec["title"],
        "category: %s" % spec["category"],
        "difficulty: %d  # %s" % (spec["difficulty"], d),
        "points: %d" % pts,
        "series: %s" % spec.get("series", ""),
        "context: RD",
        "region: %s" % spec.get("region", ""),
        "certs:",
        "  - { name: \"%s\", domain: \"%s\" }" % (spec["cert"], spec["domain"]),
        "type: %s" % kind,
        "template: %s" % spec["template"],
        "flag: { type: static, format: \"RP{...}\" }",
        "connection: \"%s\"" % conn,
        "hints:",
        "  - { level: 1, cost: 5,  text: \"%s\" }" % spec["hint1"],
        "  - { level: 2, cost: 15, text: \"%s\" }" % spec["hint2"],
        "  - { level: 3, cost: 30, text: \"%s\" }" % spec["hint3"],
        "status: published",
        "",
    ])

    readme = "\n".join([
        "# %s" % spec["title"], "",
        "- **Categoria:** %s" % spec["category"],
        "- **Dificultad:** %s" % d,
        "- **Puntos:** %d" % pts,
        "- **Serie:** %s / %s" % (spec.get("series", "-"), spec.get("region", "")),
        "- **Certificacion / Dominio:** %s -> %s" % (spec["cert"], spec["domain"]),
        "- **Tipo:** %s" % kind, "",
        "## Conexion", conn, "",
        "## Objetivo tecnico", spec["objetivo_tecnico"], "",
        "## Objetivo de investigacion", spec["objetivo_investigacion"], "",
        "## Despliegue",
        ("`docker compose up -d`" if kind == "container" else "Artefacto estatico (adjunto)."),
        "",
        "## Validacion", "```bash", "bash tests/solve.sh", "```", "",
    ])

    story = "\n".join([
        "ROOTPATH // EXPEDIENTE %s" % spec["rd"], "",
        "**Titulo:** %s" % spec["title"],
        "**Ubicacion:** %s" % spec["ubicacion"],
        "**Provincia:** %s" % spec["provincia"],
        "**Fecha:** %s" % spec["fecha"],
        "**Tipo de incidente:** %s" % spec["incidente"],
        "**Estado:** Abierto", "",
        "## Resumen", spec["resumen"], "",
        "## Evidencias disponibles",
        "".join("- %s\n" % e for e in spec["evidencias"]),
        "## Objetivo tecnico", spec["objetivo_tecnico"], "",
        "## Objetivo de investigacion", spec["objetivo_investigacion"], "",
    ])

    writeup = "\n".join([
        "# Writeup - %s" % spec["title"], "",
        "- Categoria: %s" % spec["category"],
        "- Dificultad: %s" % d,
        "- Certificacion: %s / %s" % (spec["cert"], spec["domain"]), "",
        "## Contexto", spec["resumen"], "",
        "## Solucion", solve_note, "",
        "## Flag", "```", flag, "```", "",
        "## Lecciones",
        "- Ilustra la tecnica del dominio `%s`." % spec["domain"],
        "- Validar entradas, revisar permisos y aplicar minimo privilegio.",
        "",
    ])
    return {
        "challenge.yml": yml,
        "README.md": readme,
        "story.md": story,
        "solution/writeup.md": writeup,
    }
