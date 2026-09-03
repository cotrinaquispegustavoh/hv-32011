"""Validaciones compartidas para archivos recibidos desde formularios web."""

from io import BytesIO
from zipfile import BadZipFile, ZipFile

from django.utils.text import get_valid_filename
from PIL import Image, UnidentifiedImageError


MEBIBYTE = 1024 * 1024


class UploadValidationError(ValueError):
    """Error seguro para mostrar al usuario cuando un archivo no es válido."""


_MIME_TYPES = {
    ".csv": {
        "application/csv",
        "application/octet-stream",
        "application/vnd.ms-excel",
        "text/csv",
        "text/plain",
    },
    ".doc": {"application/msword", "application/octet-stream"},
    ".docx": {
        "application/octet-stream",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/x-zip-compressed",
        "application/zip",
    },
    ".jpeg": {"application/octet-stream", "image/jpeg", "image/pjpeg"},
    ".jpg": {"application/octet-stream", "image/jpeg", "image/pjpeg"},
    ".pdf": {"application/octet-stream", "application/pdf"},
    ".png": {"application/octet-stream", "image/png"},
    ".webp": {"application/octet-stream", "image/webp"},
}


def _prepare_upload(uploaded_file, allowed_extensions, max_size):
    if not uploaded_file:
        raise UploadValidationError("No se recibió ningún archivo.")

    raw_name = str(getattr(uploaded_file, "name", "") or "")
    basename = raw_name.replace("\\", "/").rsplit("/", 1)[-1]
    safe_name = get_valid_filename(basename)
    if not safe_name:
        raise UploadValidationError("El archivo no tiene un nombre válido.")

    extension = "." + safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if extension not in allowed_extensions:
        formats = ", ".join(sorted(ext.lstrip(".").upper() for ext in allowed_extensions))
        raise UploadValidationError(f"Formato no permitido. Usa uno de estos formatos: {formats}.")

    size = getattr(uploaded_file, "size", None)
    if size is None or size <= 0:
        raise UploadValidationError("El archivo está vacío.")
    if size > max_size:
        raise UploadValidationError(
            f"El archivo excede los {max_size // MEBIBYTE} MB permitidos."
        )

    content_type = str(getattr(uploaded_file, "content_type", "") or "")
    content_type = content_type.partition(";")[0].strip().lower()
    if content_type and content_type not in _MIME_TYPES[extension]:
        raise UploadValidationError("El tipo declarado del archivo no coincide con su formato.")

    uploaded_file.name = safe_name
    return extension


def _read_upload(uploaded_file):
    try:
        uploaded_file.seek(0)
        return uploaded_file.read()
    finally:
        uploaded_file.seek(0)


def _validate_content(data, extension):
    if extension == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise UploadValidationError("El archivo no contiene un PDF válido.")
        return

    if extension == ".doc":
        if not data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
            raise UploadValidationError("El archivo no contiene un documento Word válido.")
        return

    if extension == ".docx":
        try:
            with ZipFile(BytesIO(data)) as archive:
                entries = archive.infolist()
                names = {entry.filename for entry in entries}
                required = {"[Content_Types].xml", "word/document.xml"}
                if not required.issubset(names):
                    raise UploadValidationError("El archivo no contiene un documento Word válido.")
                if len(entries) > 2_000 or sum(entry.file_size for entry in entries) > 50 * MEBIBYTE:
                    raise UploadValidationError("El documento Word contiene demasiados datos internos.")
                if archive.testzip() is not None:
                    raise UploadValidationError("El archivo Word está dañado.")
        except (BadZipFile, OSError, RuntimeError):
            raise UploadValidationError("El archivo no contiene un documento Word válido.")
        return

    if extension in {".jpg", ".jpeg", ".png", ".webp"}:
        expected_format = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".webp": "WEBP",
        }[extension]
        try:
            with Image.open(BytesIO(data)) as image:
                if image.format != expected_format:
                    raise UploadValidationError(
                        "El contenido de la imagen no coincide con su extensión."
                    )
                width, height = image.size
                if width <= 0 or height <= 0 or width * height > 40_000_000:
                    raise UploadValidationError("La imagen tiene dimensiones no permitidas.")
                image.verify()
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError):
            raise UploadValidationError("El archivo no contiene una imagen válida.")


def _validate_binary_upload(uploaded_file, allowed_extensions, max_size):
    extension = _prepare_upload(uploaded_file, allowed_extensions, max_size)
    _validate_content(_read_upload(uploaded_file), extension)
    return uploaded_file.name


def validate_document_upload(uploaded_file):
    """Admite documentos institucionales PDF o Word de hasta 15 MB."""

    return _validate_binary_upload(uploaded_file, {".pdf", ".doc", ".docx"}, 15 * MEBIBYTE)


def validate_evidence_upload(uploaded_file):
    """Admite evidencias PDF o imágenes de hasta 10 MB."""

    return _validate_binary_upload(
        uploaded_file, {".pdf", ".jpg", ".jpeg", ".png"}, 10 * MEBIBYTE
    )


def validate_portfolio_upload(uploaded_file):
    """Admite los formatos actuales del portafolio, hasta 10 MB."""

    return _validate_binary_upload(
        uploaded_file,
        {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"},
        10 * MEBIBYTE,
    )


def validate_image_upload(uploaded_file):
    """Admite imágenes JPEG, PNG o WebP de materiales, hasta 5 MB."""

    return _validate_binary_upload(
        uploaded_file,
        {".jpg", ".jpeg", ".png", ".webp"},
        5 * MEBIBYTE,
    )


def validate_csv_upload(uploaded_file):
    """Valida nombre, tamaño y codificación de un CSV de importación."""

    _prepare_upload(uploaded_file, {".csv"}, 5 * MEBIBYTE)
    data = _read_upload(uploaded_file)
    if b"\x00" in data:
        raise UploadValidationError("El CSV contiene datos binarios no permitidos.")
    try:
        data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise UploadValidationError("El CSV debe estar codificado en UTF-8.")
    return uploaded_file.name
