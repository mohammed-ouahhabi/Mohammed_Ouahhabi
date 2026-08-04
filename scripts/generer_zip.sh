#!/usr/bin/env bash
# Construit l'archive de rendu technique.
#
# L'archive est un produit de la construction, pas une source : elle n'est pas
# versionnée (cf. .gitignore). Ce script la reconstitue à l'identique, ce qui
# évite d'avoir à se souvenir de la liste des exclusions.
#
# Utilisation :
#     bash scripts/generer_zip.sh
set -euo pipefail

cd "$(dirname "$0")/.."
ARCHIVE="Mohammed_OUAHHABI_PFE.zip"

echo "Régénération du dump SQL..."
bash scripts/generer_dump.sh

echo "Construction de $ARCHIVE ..."
rm -f "$ARCHIVE"
zip -rq "$ARCHIVE" . \
  -x '*.git/*' '.git/*' \
     'venv/*' '.venv/*' \
     '*__pycache__/*' '*.pyc' \
     '.pytest_cache/*' \
     '.history/*' \
     '.claude/*' \
     'instance/*' \
     '.env' \
     '*.zip' \
     '.DS_Store' '*/.DS_Store'

echo
echo "Archive : $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"
echo
echo "Contrôle des exclusions :"
if unzip -Z1 "$ARCHIVE" | grep -qE "(^|/)(\.git|venv|__pycache__|\.pytest_cache|\.history|instance)(/|$)|\.pyc$|(^|/)\.env$"; then
    echo "  ÉCHEC : un élément qui devait être exclu se trouve dans l'archive."
    exit 1
fi
echo "  OK — aucun environnement virtuel, cache, base locale ni secret."
