import unicodedata

def normalize_text(text: str) -> str:
    """
    Convierte el texto a minúsculas y elimina tildes y diacríticos.
    Ejemplo: "Gómez" -> "gomez"
    """
    if not text:
        return ""
    text = str(text).lower()
    # Descompone los caracteres (ej. 'ó' -> 'o' + '´') y filtra los acentos
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')