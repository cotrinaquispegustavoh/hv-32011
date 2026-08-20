#!/usr/bin/env bash
# Salir inmediatamente si hay algún error
set -o errexit

echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo "🎨 Recolectando archivos estáticos (WhiteNoise)..."
python manage.py collectstatic --no-input

echo "🗄️ Aplicando migraciones a la base de datos..."
python manage.py migrate

echo "🌱 Poblando la base de datos con usuarios y secciones base..."
python manage.py seed_db