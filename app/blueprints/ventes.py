"""Analyse des ventes + catalogue Produits (front-office).

Accès : Manager, Assistant manager, Premier équipier (l'Équipier n'y a pas droit).
"""
import csv
import io
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, Response, abort
from flask_login import login_required, current_user

from ..decorators import role_requis
from ..models import (
    Produit,
    ROLE_MANAGER,
    ROLE_ASSISTANT,
    ROLE_PREMIER_EQUIPIER,
)
from ..services import kpi

bp = Blueprint("ventes", __name__)

ACCES_ANALYSE = role_requis(ROLE_MANAGER, ROLE_ASSISTANT, ROLE_PREMIER_EQUIPIER)


def _periode_depuis_requete():
    """Lit le paramètre `mois` (AAAA-MM) ou retombe sur le mois en cours."""
    mois = request.args.get("mois")
    aujourdhui = datetime.utcnow()
    if mois:
        try:
            debut = datetime.strptime(mois, "%Y-%m")
        except ValueError:
            debut = aujourdhui.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        debut = aujourdhui.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Premier jour du mois suivant.
    if debut.month == 12:
        fin = debut.replace(year=debut.year + 1, month=1)
    else:
        fin = debut.replace(month=debut.month + 1)
    return debut, fin


@bp.route("/ventes")
@login_required
@ACCES_ANALYSE
def index():
    pdv_id = current_user.point_de_vente_id
    debut, fin = _periode_depuis_requete()

    categorie = request.args.get("categorie") or None
    produit_id = request.args.get("produit_id", type=int) or None

    detail = kpi.detail_par_produit(pdv_id, debut, fin, categorie, produit_id)
    graphe = kpi.ventes_par_periode(pdv_id, debut, fin)
    paiements = kpi.repartition_paiements(pdv_id, debut, fin, categorie, produit_id)

    categories = [
        c[0]
        for c in (
            Produit.query.with_entities(Produit.categorie)
            .filter(Produit.categorie.isnot(None))
            .distinct()
            .order_by(Produit.categorie)
            .all()
        )
    ]
    produits = Produit.query.order_by(Produit.nom).all()

    return render_template(
        "ventes/index.html",
        detail=detail,
        graphe=graphe,
        paiements=paiements,
        categories=categories,
        produits=produits,
        mois_selectionne=debut.strftime("%Y-%m"),
        categorie_selectionnee=categorie,
        produit_selectionne=produit_id,
        point_de_vente=current_user.point_de_vente,
    )


@bp.route("/ventes/export")
@login_required
@ACCES_ANALYSE
def export():
    """Export CSV du détail par produit (bouton « Exporter » de la maquette)."""
    pdv_id = current_user.point_de_vente_id
    debut, fin = _periode_depuis_requete()
    detail = kpi.detail_par_produit(pdv_id, debut, fin)

    sortie = io.StringIO()
    writer = csv.writer(sortie)
    writer.writerow(["produit", "quantite", "chiffre_affaires", "part_pourcent"])
    for r in detail:
        writer.writerow([r["nom"], r["quantite"], round(r["ca"], 2), r["part"]])

    nom = f"ventes_{debut.strftime('%Y_%m')}.csv"
    return Response(
        sortie.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nom}"},
    )


@bp.route("/produits")
@login_required
def catalogue():
    """Catalogue des produits (élément « Produits » de la barre latérale)."""
    produits = Produit.query.order_by(Produit.categorie, Produit.nom).all()
    return render_template("ventes/produits.html", produits=produits)
