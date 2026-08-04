"""Tests des opportunités promotionnelles.

Chaque règle est vérifiée sur des données injectées volontairement, de sorte que
le résultat attendu soit connu à l'avance : c'est la contrepartie d'une méthode
déterministe — on peut la tester exactement.
"""
from datetime import timedelta

from app.extensions import db
from app.models import PointDeVente, Produit, Commande, LigneCommande
from app.services import opportunites, kpi


def _vendre(pdv_id, produit_id, quand, nombre, montant=20.0):
    """Crée `nombre` commandes d'une ligne à l'heure indiquée."""
    for i in range(nombre):
        c = Commande(point_de_vente_id=pdv_id,
                     date_heure=quand + timedelta(minutes=i),
                     montant_total=montant)
        c.lignes.append(LigneCommande(produit_id=produit_id, quantite=1, montant=montant))
        db.session.add(c)
    db.session.commit()


def _produit(nom):
    p = Produit(nom=nom, categorie="Test", prix_unitaire=20)
    db.session.add(p)
    db.session.flush()
    return p


# --- 1. Créneaux creux -----------------------------------------------------

def test_creneau_creux_detecte(app, db):
    pdv = PointDeVente.query.first()
    p = _produit("PizzaCreneau")
    base = kpi._maintenant().replace(minute=0, second=0, microsecond=0) - timedelta(days=3)

    # Trois créneaux chargés, un très faible : celui-ci doit ressortir.
    for heure in (12, 13, 19):
        _vendre(pdv.id_point_de_vente, p.id_produit, base.replace(hour=heure), 30)
    _vendre(pdv.id_point_de_vente, p.id_produit, base.replace(hour=16), 6)

    creux = opportunites.creneaux_creux(
        pdv.id_point_de_vente, base - timedelta(days=1), kpi._maintenant()
    )
    heures = [c["heure"] for c in creux]
    assert 16 in heures
    assert 12 not in heures and 19 not in heures

    creneau = next(c for c in creux if c["heure"] == 16)
    assert creneau["commandes"] == 6
    assert creneau["manque_a_gagner"] > 0
    assert creneau["ecart_pourcent"] > 40


def test_creneau_sous_le_minimum_de_commandes_ignore(app, db):
    """Un créneau à trop faible volume n'est pas concluant : on ne propose rien."""
    pdv = PointDeVente.query.first()
    p = _produit("PizzaRare")
    base = kpi._maintenant().replace(minute=0, second=0, microsecond=0) - timedelta(days=3)
    for heure in (12, 13, 19):
        _vendre(pdv.id_point_de_vente, p.id_produit, base.replace(hour=heure), 30)
    # 2 commandes seulement : sous le seuil de significativité.
    _vendre(pdv.id_point_de_vente, p.id_produit, base.replace(hour=15), 2)

    creux = opportunites.creneaux_creux(
        pdv.id_point_de_vente, base - timedelta(days=1), kpi._maintenant()
    )
    assert 15 not in [c["heure"] for c in creux]


# --- 2. Produits en retrait ------------------------------------------------

def test_produit_en_retrait_detecte(app, db):
    pdv = PointDeVente.query.first()
    fort1, fort2, faible = _produit("Fort1"), _produit("Fort2"), _produit("Faible")
    base = kpi._maintenant().replace(minute=0, second=0, microsecond=0) - timedelta(days=2)

    _vendre(pdv.id_point_de_vente, fort1.id_produit, base.replace(hour=12), 50)
    _vendre(pdv.id_point_de_vente, fort2.id_produit, base.replace(hour=13), 50)
    _vendre(pdv.id_point_de_vente, faible.id_produit, base.replace(hour=14), 12)

    retrait = opportunites.produits_en_retrait(
        pdv.id_point_de_vente, base - timedelta(days=1), kpi._maintenant()
    )
    noms = [p["nom"] for p in retrait]
    assert "Faible" in noms
    assert "Fort1" not in noms and "Fort2" not in noms


def test_produit_trop_peu_vendu_non_propose(app, db):
    """Sous dix ventes, l'échantillon ne permet pas de conclure."""
    pdv = PointDeVente.query.first()
    fort1, fort2, rare = _produit("Gros1"), _produit("Gros2"), _produit("Confidentiel")
    base = kpi._maintenant().replace(minute=0, second=0, microsecond=0) - timedelta(days=2)
    _vendre(pdv.id_point_de_vente, fort1.id_produit, base.replace(hour=12), 50)
    _vendre(pdv.id_point_de_vente, fort2.id_produit, base.replace(hour=13), 50)
    _vendre(pdv.id_point_de_vente, rare.id_produit, base.replace(hour=14), 3)

    retrait = opportunites.produits_en_retrait(
        pdv.id_point_de_vente, base - timedelta(days=1), kpi._maintenant()
    )
    assert "Confidentiel" not in [p["nom"] for p in retrait]


# --- 3. Associations -------------------------------------------------------

def test_association_frequente_detectee(app, db):
    pdv = PointDeVente.query.first()
    a, b, seul = _produit("Duo A"), _produit("Duo B"), _produit("Solitaire")
    base = kpi._maintenant().replace(minute=0, second=0, microsecond=0) - timedelta(days=2)

    # 15 commandes contenant A et B ensemble.
    for i in range(15):
        c = Commande(point_de_vente_id=pdv.id_point_de_vente,
                     date_heure=base.replace(hour=12) + timedelta(minutes=i),
                     montant_total=40)
        c.lignes.append(LigneCommande(produit_id=a.id_produit, quantite=1, montant=20))
        c.lignes.append(LigneCommande(produit_id=b.id_produit, quantite=1, montant=20))
        db.session.add(c)
    db.session.commit()
    # Et des commandes ne contenant qu'un seul produit.
    _vendre(pdv.id_point_de_vente, seul.id_produit, base.replace(hour=19), 20)

    assos = opportunites.associations_produits(
        pdv.id_point_de_vente, base - timedelta(days=1), kpi._maintenant()
    )
    paires = [set(x["produits"]) for x in assos]
    assert {"Duo A", "Duo B"} in paires

    duo = next(x for x in assos if set(x["produits"]) == {"Duo A", "Duo B"})
    assert duo["commandes"] == 15
    # Le panier de ces commandes (40 €) dépasse le panier global.
    assert duo["ecart_panier"] > 0


# --- Structure et accès ----------------------------------------------------

def test_analyser_renvoie_la_structure_attendue(app, db):
    pdv = PointDeVente.query.first()
    r = opportunites.analyser(pdv.id_point_de_vente, jours=90)
    for cle in ("periode", "creneaux_creux", "produits_en_retrait",
                "associations", "graphe_heures", "graphe_produits"):
        assert cle in r
    assert isinstance(r["creneaux_creux"], list)


def test_acces_opportunites_selon_le_role(client, db):
    """Même niveau que l'analyse des ventes : l'équipier n'y a pas accès."""
    from tests.conftest import connexion

    connexion(client, "manager@test.fr")
    assert client.get("/opportunites").status_code == 200
    client.get("/logout")

    connexion(client, "premier@test.fr")
    assert client.get("/opportunites").status_code == 200
    client.get("/logout")

    connexion(client, "equipier@test.fr")
    assert client.get("/opportunites").status_code == 403


# --------------------------------------------------------------------------
# Cohérence entre le graphique et la règle qu'il annonce
#
# L'en-tête du graphique annonce « CA inférieur à 60 % de la moyenne horaire ».
# Le détail sous le graphique ne montre que les trois créneaux les plus
# pénalisants : c'est un choix d'affichage. Le graphique, lui, doit signaler
# TOUS les créneaux sous le seuil, sans quoi il contredit son propre libellé.
# --------------------------------------------------------------------------

def test_le_graphique_signale_tous_les_creneaux_sous_le_seuil(app, db):
    pdv = PointDeVente.query.first()
    p = _produit("PizzaGraphique")
    base = kpi._maintenant().replace(minute=0, second=0, microsecond=0) - timedelta(days=3)
    debut, fin = base, base + timedelta(days=1)

    # Huit heures normales, puis quatre heures creuses : une de plus que les
    # trois que retient la liste détaillée.
    for heure in range(11, 19):
        _vendre(pdv.id_point_de_vente, p.id_produit, base.replace(hour=heure), 20)
    for heure in range(19, 23):
        _vendre(pdv.id_point_de_vente, p.id_produit, base.replace(hour=heure), 6)

    creux = opportunites.creneaux_creux(pdv.id_point_de_vente, debut, fin)
    graphe = opportunites.serie_ca_par_heure(pdv.id_point_de_vente, debut, fin)

    # La liste détaillée reste plafonnée à trois entrées.
    assert len(creux) == 3

    # Le graphique, lui, applique la règle annoncée, sans plafond.
    seuil = graphe["seuil"]
    assert graphe["creux"] == [0 < v < seuil for v in graphe["valeurs"]]
    assert sum(graphe["creux"]) == 4, "les quatre créneaux sous le seuil sont signalés"
