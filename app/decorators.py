"""Décorateurs de contrôle d'accès (gestion des rôles « à la main »).

On n'utilise pas de librairie de permissions : un simple décorateur vérifie le
rôle de l'utilisateur connecté avant d'exécuter la vue. C'est volontaire —
la logique reste lisible et défendable à l'oral.

Matrice d'accès (cf. cahier des charges) :

    Rôle               | Tableau de bord | Analyse | Back-office / Import
    -------------------|-----------------|---------|---------------------
    Manager            | oui             | oui     | oui
    Assistant manager  | oui             | oui     | oui
    Premier équipier   | oui             | oui     | non
    Équipier           | oui             | non     | non
"""
from functools import wraps

from flask import abort
from flask_login import current_user


def role_requis(*roles):
    """Autorise l'accès uniquement aux utilisateurs dont le rôle est listé.

    Utilisation :
        @role_requis(ROLE_MANAGER, ROLE_ASSISTANT)
        def ma_vue(): ...
    """

    def decorateur(vue):
        @wraps(vue)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                # 403 : connecté mais rôle insuffisant.
                abort(403)
            return vue(*args, **kwargs)

        return wrapper

    return decorateur
