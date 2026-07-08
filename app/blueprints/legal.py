"""Pages légales / RGPD : mentions légales, CGU, politique cookies.

Accessibles sans authentification (obligation légale : consultables par tous).
"""
from flask import Blueprint, render_template

bp = Blueprint("legal", __name__)


@bp.route("/mentions-legales")
def mentions():
    return render_template("legal/mentions.html")


@bp.route("/cgu")
def cgu():
    return render_template("legal/cgu.html")


@bp.route("/confidentialite")
def confidentialite():
    return render_template("legal/confidentialite.html")
