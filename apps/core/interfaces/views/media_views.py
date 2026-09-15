"""Entrega autorizada de archivos subidos por usuarios.

Las URLs existentes bajo ``/media/`` se conservan para no romper referencias ya
guardadas. Django decide si el usuario puede ver el archivo y, opcionalmente,
delega la transferencia a Nginx mediante ``X-Accel-Redirect``.
"""

import mimetypes
import os
import posixpath
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse
from django.utils import timezone
from django.utils._os import safe_join
from django.utils.http import content_disposition_header

from apps.core.infrastructure.models import InstitutionalAnnouncement
from apps.discipline.infrastructure.models import Evidence
from apps.documents.infrastructure.models import InstitutionalDocument
from apps.portfolio.infrastructure.models import PortfolioItem
from apps.users.permissions import has_permission


def _normalized_media_path(path):
    """Rechaza rutas absolutas, traversal y variantes ambiguas."""

    raw_path = str(path or "").replace("\\", "/")
    normalized = posixpath.normpath(raw_path).lstrip("/")
    if (
        not raw_path
        or raw_path.startswith("/")
        or normalized in {"", "."}
        or normalized.startswith("../")
        or normalized != raw_path
    ):
        raise Http404("Archivo no encontrado.")
    return normalized


def _can_access_announcement(user, path):
    announcement = InstitutionalAnnouncement.objects.filter(image=path).first()
    if not announcement:
        return False
    if user.is_superuser or user.role in {"DIRECTOR", "SUPERUSER"}:
        return True
    if not announcement.is_active:
        return False
    if announcement.valid_until and announcement.valid_until < timezone.localdate():
        return False
    return announcement.is_visible_to(user)


def _can_access_document(user, path):
    if not has_permission(user, "documents.view"):
        return False
    document = (
        InstitutionalDocument.objects.filter(current_file=path).first()
        or InstitutionalDocument.objects.filter(versions__file=path).distinct().first()
    )
    if not document:
        return False
    if user.is_superuser or user.role in {"DIRECTOR", "SUBDIRECTOR", "SUPERUSER"}:
        return True
    if document.access_level == "PUBLIC":
        return True
    return document.access_level == "STAFF" and user.role in {"DOCENTE", "APOYO"}


def _can_access_portfolio(user, path):
    item = PortfolioItem.objects.filter(file=path).first()
    if not item:
        return False
    if has_permission(user, "portfolio.review"):
        return True
    return has_permission(user, "portfolio.own") and item.teacher_id == user.pk


def _can_access_evidence(user, path):
    evidence = Evidence.objects.select_related("incident").filter(
        file=path,
        incident__is_deleted=False,
    ).first()
    if not evidence:
        return False
    if has_permission(user, "discipline.review"):
        return True
    return (
        has_permission(user, "discipline.create")
        and evidence.incident.reported_by_id == user.pk
    )


def _can_access_media(user, path):
    if path.startswith(("materials/", "manuals/")):
        return has_permission(user, "warehouse.view")
    if path.startswith("institutional_announcements/"):
        return _can_access_announcement(user, path)
    if path.startswith("institutional_docs/"):
        return _can_access_document(user, path)
    if path.startswith("portfolio_files/"):
        return _can_access_portfolio(user, path)
    if path.startswith("discipline_evidences/"):
        return _can_access_evidence(user, path)
    return False


@login_required(login_url="/auth/login/")
def protected_media_view(request, path):
    """Entrega un archivo solo después de validar el acceso funcional."""

    normalized_path = _normalized_media_path(path)
    if not _can_access_media(request.user, normalized_path):
        # Un 404 evita confirmar a una cuenta no autorizada que el archivo existe.
        raise Http404("Archivo no encontrado.")

    content_type = mimetypes.guess_type(normalized_path)[0] or "application/octet-stream"
    filename = posixpath.basename(normalized_path)
    disposition = content_disposition_header(False, filename)

    if settings.PROTECTED_MEDIA_USE_X_ACCEL:
        response = HttpResponse(content_type=content_type)
        response["X-Accel-Redirect"] = (
            f"{settings.PROTECTED_MEDIA_INTERNAL_URL.rstrip('/')}/"
            f"{quote(normalized_path, safe='/')}"
        )
        if disposition:
            response["Content-Disposition"] = disposition
        response["Cache-Control"] = "private, no-store"
        return response

    try:
        absolute_path = safe_join(settings.MEDIA_ROOT, normalized_path)
    except ValueError as exc:
        raise Http404("Archivo no encontrado.") from exc
    if not os.path.isfile(absolute_path):
        raise Http404("Archivo no encontrado.")

    response = FileResponse(open(absolute_path, "rb"), content_type=content_type)
    if disposition:
        response["Content-Disposition"] = disposition
    response["Cache-Control"] = "private, no-store"
    return response
