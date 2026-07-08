#!/usr/bin/env bash
# Génère un export SQL (dump) de la base, quel que soit le moteur.
#
#   - Développement (SQLite)  : ./scripts/generer_dump.sh
#   - Production  (PostgreSQL) : DATABASE_URL=postgresql://... ./scripts/generer_dump.sh
#
# Le fichier produit est dump.sql à la racine du projet.
set -euo pipefail

SORTIE="${1:-dump.sql}"

if [[ -n "${DATABASE_URL:-}" && "$DATABASE_URL" == postgres* ]]; then
  echo "Export PostgreSQL vers $SORTIE ..."
  pg_dump "$DATABASE_URL" > "$SORTIE"
else
  DB_PATH="instance/pilotage.db"
  if [[ ! -f "$DB_PATH" ]]; then
    echo "Base SQLite introuvable ($DB_PATH). Lancez d'abord les migrations et le seed." >&2
    exit 1
  fi
  echo "Export SQLite ($DB_PATH) vers $SORTIE ..."
  # On utilise le module sqlite3 de Python (toujours disponible) plutôt que la
  # CLI sqlite3, qui n'est pas installée partout.
  python3 - "$DB_PATH" "$SORTIE" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
with open(sys.argv[2], "w", encoding="utf-8") as f:
    for ligne in conn.iterdump():
        f.write(ligne + "\n")
conn.close()
PY
fi

echo "Dump généré : $SORTIE"
