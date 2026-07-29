"""Génère un jeu de données de démonstration représentatif.

Aucune donnée réelle de l'entreprise n'est utilisée : le jeu reproduit la
STRUCTURE rencontrée en magasin (produits type pizzeria, pics midi/soir), avec
des volumes proches des maquettes (~48 000 € de CA sur 30 jours, panier ~36 €).

Utilisation :
    flask seed                 # via la commande CLI
    python -m scripts.seed     # en direct
"""
import random
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import (
    PointDeVente,
    Utilisateur,
    Produit,
    Commande,
    LigneCommande,
    Vente,
    ImportFichier,
    ImportTemporaire,
    ROLE_MANAGER,
    ROLE_ASSISTANT,
    ROLE_PREMIER_EQUIPIER,
    ROLE_EQUIPIER,
)

# Répartition réaliste des modes de paiement (cf. système source Pulse).
MODES_PAIEMENT = ["Carte", "Espèces", "Ticket resto"]
POIDS_PAIEMENT = [60, 30, 10]

# Graine fixe : jeu reproductible d'une exécution à l'autre.
random.seed(42)

PRODUITS = [
    # (nom, catégorie, prix, poids de popularité)
    ("Reine", "Pizza", 13.90, 30),
    ("Pepperoni", "Pizza", 14.90, 26),
    ("4 Fromages", "Pizza", 15.90, 20),
    ("Végétarienne", "Pizza", 13.50, 14),
    ("Calzone", "Pizza", 14.50, 12),
    ("Margherita", "Pizza", 11.90, 10),
    ("Boisson 33cl", "Boisson", 2.50, 28),
    ("Tiramisu", "Dessert", 4.90, 12),
]

# Répartition horaire (poids) : pics le midi (12-13h) et le soir (19-21h).
POIDS_HORAIRE = {
    11: 3, 12: 12, 13: 10, 14: 4, 15: 2, 16: 2,
    17: 3, 18: 6, 19: 12, 20: 14, 21: 10, 22: 4,
}


def _choisir_produit():
    noms = [p[0] for p in PRODUITS]
    poids = [p[3] for p in PRODUITS]
    return random.choices(noms, weights=poids, k=1)[0]


def _choisir_heure():
    heures = list(POIDS_HORAIRE.keys())
    poids = list(POIDS_HORAIRE.values())
    return random.choices(heures, weights=poids, k=1)[0]


def executer_seed():
    """Vide puis recharge les données de démonstration."""
    # On efface les données transactionnelles et les comptes de démo, dans
    # l'ordre des dépendances (indispensable en PostgreSQL, où les clés
    # étrangères sont strictement appliquées) : import_fichier référence
    # utilisateur, vente et ligne_commande référencent commande.
    ImportTemporaire.query.delete()
    ImportFichier.query.delete()
    Vente.query.delete()
    LigneCommande.query.delete()
    Commande.query.delete()
    Produit.query.delete()
    Utilisateur.query.delete()
    PointDeVente.query.delete()
    db.session.commit()

    # 1. Point de vente
    pdv = PointDeVente(nom="Chatou", ville="Chatou")
    db.session.add(pdv)
    db.session.flush()

    # 2. Utilisateurs (un par rôle, mot de passe commun de démo)
    comptes = [
        ("Ahmed O.", "manager@pdv-chatou.fr", ROLE_MANAGER),
        ("Responsable Chatou", "responsable@pdv-chatou.fr", ROLE_MANAGER),
        ("Adjoint Chatou", "adjoint@pdv-chatou.fr", ROLE_ASSISTANT),
        ("Premier équipier", "premier@pdv-chatou.fr", ROLE_PREMIER_EQUIPIER),
        ("Équipier", "equipier@pdv-chatou.fr", ROLE_EQUIPIER),
    ]
    for nom, email, role in comptes:
        u = Utilisateur(nom=nom, email=email, role=role, actif=True,
                        point_de_vente_id=pdv.id_point_de_vente)
        u.definir_mot_de_passe("motdepasse123")
        db.session.add(u)

    # 3. Produits
    produits = {}
    for nom, cat, prix, _ in PRODUITS:
        p = Produit(nom=nom, categorie=cat, prix_unitaire=prix)
        db.session.add(p)
        db.session.flush()
        produits[nom] = p

    # 4. Commandes + lignes sur 75 jours (dont les 30 derniers pour le dashboard)
    prix_par_nom = {nom: prix for nom, _, prix, _ in PRODUITS}
    aujourdhui = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    debut = aujourdhui - timedelta(days=75)

    jour = debut
    nb_commandes = 0
    while jour <= aujourdhui:
        # Week-end un peu plus chargé.
        base = 48 if jour.weekday() >= 4 else 40
        commandes_du_jour = random.randint(base - 6, base + 6)
        for _ in range(commandes_du_jour):
            heure = _choisir_heure()
            minute = random.randint(0, 59)
            dh = jour.replace(hour=heure, minute=minute)
            commande = Commande(point_de_vente_id=pdv.id_point_de_vente,
                                date_heure=dh, montant_total=0)
            db.session.add(commande)
            db.session.flush()

            total = 0.0
            for _ in range(random.randint(1, 3)):  # 1 à 3 lignes par commande
                nom = _choisir_produit()
                quantite = random.randint(1, 2)
                montant = round(prix_par_nom[nom] * quantite, 2)
                commande.lignes.append(LigneCommande(
                    produit_id=produits[nom].id_produit,
                    quantite=quantite, montant=montant))
                total += montant
            commande.montant_total = round(total, 2)

            # Encaissement associé (table vente, issue de Pulse).
            mode = random.choices(MODES_PAIEMENT, weights=POIDS_PAIEMENT, k=1)[0]
            db.session.add(Vente(
                commande_id=commande.id_commande,
                montant=commande.montant_total,
                date_vente=commande.date_heure,
                mode_paiement=mode,
            ))
            nb_commandes += 1

        jour += timedelta(days=1)

    db.session.commit()
    print(f"{nb_commandes} commandes générées sur 75 jours.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        executer_seed()
