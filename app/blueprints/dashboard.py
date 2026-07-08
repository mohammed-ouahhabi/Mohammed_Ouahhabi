"""Tableau de bord (front-office) — accessible à tous les rôles."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..services import kpi

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@bp.route("/tableau-de-bord")
@login_required
def index():
    pdv_id = current_user.point_de_vente_id
    # Période par défaut : 30 derniers jours (cf. maquette).
    resume = kpi.resume_dashboard(pdv_id, jours=30)
    return render_template(
        "dashboard/index.html",
        resume=resume,
        point_de_vente=current_user.point_de_vente,
    )
