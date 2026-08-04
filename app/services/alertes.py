"""Service d'alertes — couche « aide à la décision » (lecture seule).

Signale automatiquement les situations à surveiller, à partir des données déjà
en base. Aucune nouvelle table : on lit et on compare des périodes.

Trois règles, dont les seuils sont des constantes ajustables ci-dessous :
  1. Produit en décrochage   : quantité en forte baisse vs période précédente.
  2. Chute de chiffre d'affaires : journée nettement sous la moyenne du même jour.
  3. Pic d'activité inhabituel : créneau horaire nettement au-dessus de l'habitude.

Le CA n'est jamais recalculé ici : on réutilise les fonctions de services/kpi.py.
"""
from datetime import timedelta

from ..extensions import db
from ..models import Commande
from . import kpi

# --- Seuils (faciles à ajuster) -------------------------------------------
SEUIL_DECROCHAGE = 0.30           # baisse > 30 % de la quantité vendue
VOLUME_MIN_DECROCHAGE = 10        # au moins 10 ventes avant, pour éviter le bruit
SEUIL_CHUTE_CA = 0.25            # journée > 25 % sous la moyenne du jour de semaine
SEUIL_CHUTE_CA_CRITIQUE = 0.40  # au-delà de 40 % : critique
SEUIL_PIC = 0.50                # créneau > 50 % au-dessus de la moyenne habituelle
MIN_OCCURRENCES_JOUR = 2        # nb mini de jours de même type pour comparer
MIN_MOYENNE_PIC = 2             # moyenne mini d'un créneau pour parler de « pic »

# Priorité d'affichage des niveaux (critique en premier).
_ORDRE_NIVEAU = {"critique": 0, "attention": 1, "info": 2}

# Noms de jours en français : strftime('%A') dépend de la locale du serveur et
# renvoie l'anglais par défaut sur l'hébergement. On ne laisse pas ce hasard
# décider de la langue affichée à l'utilisateur.
JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def calculer_alertes(point_de_vente_id, jours=30):
    """Renvoie la liste des alertes pour un PDV sur la période. Vide si rien."""
    fin = kpi._maintenant()
    debut = fin - timedelta(days=jours)
    debut_prec = debut - timedelta(days=jours)

    alertes = []
    alertes += _produits_en_decrochage(point_de_vente_id, debut, fin, debut_prec)
    alertes += _chute_ca(point_de_vente_id, debut, fin)
    alertes += _pics_inhabituels(point_de_vente_id, debut, fin)

    alertes.sort(key=lambda a: _ORDRE_NIVEAU.get(a["niveau"], 3))
    return alertes


def _produits_en_decrochage(pdv_id, debut, fin, debut_prec):
    """Produits dont la quantité vendue chute fortement vs période précédente."""
    courant = {r["nom"]: r["quantite"] for r in kpi.detail_par_produit(pdv_id, debut, fin)}
    precedent = {r["nom"]: r["quantite"] for r in kpi.detail_par_produit(pdv_id, debut_prec, debut)}

    alertes = []
    for nom, qte_prec in precedent.items():
        if qte_prec < VOLUME_MIN_DECROCHAGE:
            continue  # volume trop faible : on ignore (bruit)
        qte_cour = courant.get(nom, 0)
        baisse = (qte_prec - qte_cour) / qte_prec
        if baisse > SEUIL_DECROCHAGE:
            alertes.append({
                "type": "produit_decrochage",
                "niveau": "attention",
                "titre": f"Produit en décrochage : {nom}",
                "message": (
                    f"{nom} : {qte_cour} ventes sur la période, contre {qte_prec} "
                    f"sur la précédente (−{round(baisse * 100)} %)."
                ),
            })
    return alertes


def _chute_ca(pdv_id, debut, fin):
    """Journées dont le CA est nettement sous la moyenne du même jour de semaine."""
    par_jour = kpi.ca_par_jour(pdv_id, debut, fin)
    if not par_jour:
        return []

    # La journée en cours est incomplète : la comparer à des journées entières
    # la ferait mécaniquement ressortir en chute, quel que soit le commerce. On
    # l'écarte plutôt que de produire une alerte structurellement fausse.
    jour_en_cours = fin.date()
    par_jour = {j: ca for j, ca in par_jour.items() if j != jour_en_cours}
    if not par_jour:
        return []

    # Moyenne du CA par jour de semaine (0 = lundi ... 6 = dimanche).
    par_semaine = {}
    for jour, ca in par_jour.items():
        par_semaine.setdefault(jour.weekday(), []).append(ca)

    alertes = []
    # On n'examine que les jours récents (7 derniers jours de la période).
    jours_recents = sorted(par_jour.keys())[-7:]
    for jour in jours_recents:
        valeurs = par_semaine.get(jour.weekday(), [])
        # Moyenne des AUTRES jours du même type (au moins MIN_OCCURRENCES).
        autres = [v for v in valeurs if v != par_jour[jour]] or valeurs
        if len(valeurs) < MIN_OCCURRENCES_JOUR + 1:
            continue
        moyenne = sum(autres) / len(autres)
        if moyenne <= 0:
            continue
        ecart = (moyenne - par_jour[jour]) / moyenne
        if ecart > SEUIL_CHUTE_CA:
            niveau = "critique" if ecart > SEUIL_CHUTE_CA_CRITIQUE else "attention"
            alertes.append({
                "type": "chute_ca",
                "niveau": niveau,
                "titre": f"Chute de CA le {jour.strftime('%d/%m')}",
                "message": (
                    f"CA de {round(par_jour[jour])} € le {jour.strftime('%d/%m')}, "
                    f"soit −{round(ecart * 100)} % sous la moyenne des "
                    f"{JOURS_FR[jour.weekday()]}s récents (~{round(moyenne)} €)."
                ),
            })
    return alertes


def _pics_inhabituels(pdv_id, debut, fin):
    """Créneau horaire du dernier jour nettement au-dessus de sa moyenne habituelle."""
    commandes = (
        db.session.query(Commande.date_heure)
        .filter(Commande.point_de_vente_id == pdv_id)
        .filter(Commande.date_heure >= debut, Commande.date_heure < fin)
        .all()
    )
    if not commandes:
        return []

    # Comptage des commandes par (date, heure).
    par_date_heure = {}
    for (dh,) in commandes:
        if dh is None:
            continue
        cle = (dh.date(), dh.hour)
        par_date_heure[cle] = par_date_heure.get(cle, 0) + 1

    if not par_date_heure:
        return []

    dates = {d for (d, _) in par_date_heure}
    dernier_jour = max(dates)
    autres_jours = [d for d in dates if d != dernier_jour]
    if not autres_jours:
        return []

    alertes = []
    meilleur = None
    for heure in range(24):
        counts_autres = [par_date_heure.get((d, heure), 0) for d in autres_jours]
        moyenne = sum(counts_autres) / len(counts_autres)
        actuel = par_date_heure.get((dernier_jour, heure), 0)
        if moyenne >= MIN_MOYENNE_PIC and actuel > moyenne * (1 + SEUIL_PIC):
            depassement = (actuel - moyenne) / moyenne
            if meilleur is None or depassement > meilleur["depassement"]:
                meilleur = {"heure": heure, "actuel": actuel, "moyenne": moyenne,
                            "depassement": depassement}
    if meilleur:
        alertes.append({
            "type": "pic_activite",
            "niveau": "info",
            "titre": f"Pic d'activité à {meilleur['heure']}h",
            "message": (
                f"{meilleur['actuel']} commandes à {meilleur['heure']}h le "
                f"{dernier_jour.strftime('%d/%m')}, soit +{round(meilleur['depassement'] * 100)} % "
                f"au-dessus de l'habitude (~{round(meilleur['moyenne'], 1)})."
            ),
        })
    return alertes
