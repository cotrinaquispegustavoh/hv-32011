#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

APP_DIR="${INTRANET_APP_DIR:-/var/www/intranet-hv}"
BACKUP_ROOT="${INTRANET_BACKUP_ROOT:-/var/backups/intranet-hv}"
RETENTION_DAYS="${INTRANET_BACKUP_RETENTION_DAYS:-14}"
OFFSITE_REMOTE="${INTRANET_BACKUP_RCLONE_REMOTE:-}"

APP_DIR="$(readlink -f -- "$APP_DIR")"
BACKUP_ROOT="$(readlink -m -- "$BACKUP_ROOT")"

if [[ ! -f "$APP_DIR/manage.py" || ! -d "$APP_DIR/media" ]]; then
    echo "La ruta de la aplicación no es válida: $APP_DIR" >&2
    exit 1
fi
case "$BACKUP_ROOT" in
    /|/var|/var/backups|"")
        echo "La ruta de respaldo es demasiado amplia: $BACKUP_ROOT" >&2
        exit 1
        ;;
esac
if [[ ! "$RETENTION_DAYS" =~ ^[0-9]+$ ]] || (( RETENTION_DAYS < 1 )); then
    echo "INTRANET_BACKUP_RETENTION_DAYS debe ser un entero mayor que cero." >&2
    exit 1
fi

mkdir -p -- "$BACKUP_ROOT"
chmod 700 -- "$BACKUP_ROOT"
exec 9>"$BACKUP_ROOT/.backup.lock"
flock -n 9 || { echo "Ya existe otro respaldo en ejecución." >&2; exit 1; }

# Lee la conexión ya interpretada por Django. La contraseña viaja por una
# tubería privada y nunca aparece en la línea de comandos.
mapfile -d '' -t database_parts < <(
    cd "$APP_DIR"
    "$APP_DIR/venv/bin/python" -c '
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from django.conf import settings

database = settings.DATABASES["default"]
if "postgresql" not in database["ENGINE"]:
    raise SystemExit("La base configurada no es PostgreSQL")
options = database.get("OPTIONS", {})
values = (
    database.get("HOST") or "localhost",
    str(database.get("PORT") or 5432),
    database.get("USER") or "",
    database.get("PASSWORD") or "",
    database.get("NAME") or "",
    options.get("sslmode", ""),
)
sys.stdout.write("\0".join(values) + "\0")
'
)
if (( ${#database_parts[@]} != 6 )); then
    echo "No se pudo interpretar DATABASE_URL." >&2
    exit 1
fi
export PGHOST="${database_parts[0]}"
export PGPORT="${database_parts[1]}"
export PGUSER="${database_parts[2]}"
export PGPASSWORD="${database_parts[3]}"
export PGDATABASE="${database_parts[4]}"
if [[ -n "${database_parts[5]}" ]]; then
    export PGSSLMODE="${database_parts[5]}"
fi

stamp="$(date -u +'%Y-%m-%dT%H%M%SZ')"
pending_dir="$(mktemp -d "$BACKUP_ROOT/.pending.XXXXXX")"
final_dir="$BACKUP_ROOT/$stamp"

cleanup() {
    if [[ -n "${pending_dir:-}" && -d "$pending_dir" ]]; then
        rm -rf -- "$pending_dir"
    fi
}
trap cleanup EXIT

pg_dump \
    --format=custom \
    --compress=9 \
    --file="$pending_dir/database.dump"
unset PGPASSWORD

tar \
    --create \
    --gzip \
    --file="$pending_dir/media.tar.gz" \
    --directory="$APP_DIR" \
    media

{
    echo "created_at_utc=$stamp"
    echo "git_commit=$(git -C "$APP_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
    echo "hostname=$(hostname)"
} > "$pending_dir/manifest.txt"

(
    cd "$pending_dir"
    sha256sum database.dump media.tar.gz manifest.txt > SHA256SUMS
)

mv -- "$pending_dir" "$final_dir"
pending_dir=""

if [[ -n "$OFFSITE_REMOTE" ]]; then
    command -v rclone >/dev/null 2>&1 || {
        echo "Se configuró copia externa, pero rclone no está instalado." >&2
        exit 1
    }
    rclone copy "$final_dir" "${OFFSITE_REMOTE%/}/$stamp" --checksum
fi

# Solo elimina carpetas con el formato exacto generado por este script y que
# estén dentro del directorio de respaldo previamente validado.
find "$BACKUP_ROOT" \
    -mindepth 1 -maxdepth 1 -type d \
    -name '????-??-??T??????Z' -mtime "+$RETENTION_DAYS" \
    -exec find '{}' -depth -delete ';'

echo "Respaldo completado: $final_dir"
