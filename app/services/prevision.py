"""Service de prévision d'affluence — couche « aide à la décision » (lecture seule).

Méthode assumée : statistique simple, PAS de machine learning.
L'affluence prévue d'un créneau (jour de semaine × heure) est la MOYENNE des
commandes observées sur ce même créneau dans l'historique du point de vente.

En une phrase : « on estime chaque créneau par la moyenne des créneaux
équivalents passés (même jour de la semaine, même heure). »

Choix défendable : robuste, transparent, explicable — et suffisant pour un besoin
de staffing. Le machine learning est une évolution future, non nécessaire ici.
"""
from datetime import timedelta

from ..extensions import db
from ..models import Commande
from . import kpi

# Plage horaire d'ouverture affichée dans la prévision.
HEURE_OUVERTURE = 10
HEURE_FERMETURE = 23

# Noms de jours pour l'affichage.
JOURS_FR = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]


def moyenne_par_creneau(point_de_vente_id, jours_historique=None):
    """Renvoie {(jour_semaine, heure): moyenne de commandes}.

    jour_semaine : 0 = lundi ... 6 = dimanche.
    La moyenne d'un créneau = total des commandes de ce créneau / nombre de jours
    de ce type présents dans l'historique (les jours à 0 comptent, pour ne pas
    surestimer).
    """
    q = db.session.query(Commande.date_heure).filter(
        Commande.point_de_vente_id == point_de_vente_id
    )
    if jours_historique:
        limite = kpi._maintenant() - timedelta(days=jours_historique)
        q = q.filter(Commande.date_heure >= limite)

    commandes = q.all()

    # Comptage par (date, heure) et recensement des dates par jour de semaine.
    par_date_heure = {}
    dates_par_semaine = {}
    for (dh,) in commandes:
        if dh is None:
            continue
        d = dh.date()
        par_date_heure[(d, dh.hour)] = par_date_heure.get((d, dh.hour), 0) + 1
        dates_par_semaine.setdefault(d.weekday(), set()).add(d)

    moyennes = {}
    for jsem, dates in dates_par_semaine.items():
        n = len(dates)
        for heure in range(24):
            total = sum(par_date_heure.get((d, heure), 0) for d in dates)
            if total:
                moyennes[(jsem, heure)] = total / n
    return moyennes


def prevoir_7_jours(point_de_vente_id, jours_historique=None):
    """Prévision de l'affluence par créneau pour les 7 prochains jours.

    Renvoie :
      {
        "jours":  [ {date, label, total, par_heure: {heure: estimation}}, ... ],
        "labels": [...],  # pour un graphique (un point par jour)
        "valeurs":[...],  # total de commandes estimé par jour
      }
    """
    moyennes = moyenne_par_creneau(point_de_vente_id, jours_historique)
    aujourdhui = kpi._maintenant().date()

    jours = []
    for i in range(1, 8):  # J+1 à J+7
        jour = aujourdhui + timedelta(days=i)
        jsem = jour.weekday()
        par_heure = {}
        for heure in range(HEURE_OUVERTURE, HEURE_FERMETURE + 1):
            estimation = moyennes.get((jsem, heure), 0)
            par_heure[heure] = round(estimation, 1)
        total = round(sum(par_heure.values()))
        jours.append({
            "date": jour,
            "label": f"{JOURS_FR[jsem]} {jour.strftime('%d/%m')}",
            "total": total,
            "par_heure": par_heure,
        })

    return {
        "jours": jours,
        "labels": [j["label"] for j in jours],
        "valeurs": [j["total"] for j in jours],
    }
