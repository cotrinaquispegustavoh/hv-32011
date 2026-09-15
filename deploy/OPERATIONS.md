# Operación segura del VPS

## Archivos protegidos

Las URLs `/media/...` pasan primero por Django. Después de instalar el bloque
`deploy/nginx/protected-media.conf` dentro del `server` HTTPS, añadir a `.env`:

```dotenv
PROTECTED_MEDIA_USE_X_ACCEL=True
TRUSTED_PROXY_IPS=127.0.0.1,::1
```

Validar y recargar Nginx antes de reiniciar Daphne:

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl restart intranet-hv
```

Una petición anónima a `/media/...` debe redirigir al login. Una cuenta sin el
permiso correspondiente debe recibir 404. No se debe crear un `location
/media/` público en Nginx.

## Respaldo diario

El respaldo incluye un `pg_dump` en formato custom, la carpeta `media`, el
commit desplegado y sumas SHA-256. La copia local predeterminada queda en
`/var/backups/intranet-hv` con retención de 14 días.

Para que también exista una copia fuera del VPS, configurar un remote de
`rclone` —preferiblemente cifrado— y crear `/etc/intranet-hv-backup.env`:

```dotenv
INTRANET_BACKUP_RETENTION_DAYS=14
INTRANET_BACKUP_RCLONE_REMOTE=hv-backups-crypt:intranet-hv
```

El archivo debe pertenecer a root y no ser legible por otros usuarios:

```bash
sudo chown root:root /etc/intranet-hv-backup.env
sudo chmod 600 /etc/intranet-hv-backup.env
```

Instalar el servicio y ejecutar una primera copia manual:

```bash
sudo chmod 750 deploy/backup_intranet.sh
sudo install -m 644 deploy/systemd/intranet-hv-backup.service /etc/systemd/system/intranet-hv-backup.service
sudo install -m 644 deploy/systemd/intranet-hv-backup.timer /etc/systemd/system/intranet-hv-backup.timer
sudo systemctl daemon-reload
sudo systemctl enable --now intranet-hv-backup.timer
sudo systemctl start intranet-hv-backup.service
sudo systemctl status intranet-hv-backup.service --no-pager
sudo systemctl list-timers intranet-hv-backup.timer --no-pager
```

Si la copia externa aún no está configurada, el respaldo local funciona
dejando `INTRANET_BACKUP_RCLONE_REMOTE` vacío. Eso protege de errores de la
aplicación, pero no de la pérdida completa del VPS.

## Prueba de restauración

La restauración debe ensayarse en una base separada, nunca directamente sobre
producción. Verificar primero las sumas:

```bash
cd /var/backups/intranet-hv/FECHA_DEL_RESPALDO
sha256sum --check SHA256SUMS
createdb intranet_hv_restore_test
pg_restore --exit-on-error --no-owner --dbname=intranet_hv_restore_test database.dump
```

Para inspeccionar los archivos sin reemplazar `media`:

```bash
sudo mkdir -p /var/tmp/intranet-hv-restore-test
sudo tar -xzf media.tar.gz -C /var/tmp/intranet-hv-restore-test
```

Eliminar la base y el directorio de prueba solo después de verificar el
resultado. Una restauración real requiere detener el servicio y una ventana de
mantenimiento aprobada.
