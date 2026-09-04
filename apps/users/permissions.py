"""Catálogo central de permisos funcionales y compatibilidad con permisos antiguos."""

GRANULAR_PERMISSIONS_MARKER = 'permissions:v2'

PERMISSION_GROUPS = (
    {
        'label': 'Almacén e inventario',
        'icon': 'fa-solid fa-boxes-stacked',
        'permissions': (
            ('warehouse.view', 'Ver catálogo', 'Consultar materiales, fotografías y disponibilidad.'),
            ('warehouse.request', 'Solicitar materiales', 'Crear solicitudes y consultar el historial propio.'),
            ('warehouse.manage', 'Gestionar inventario', 'Crear, importar, editar y eliminar materiales.'),
            ('warehouse.dispatch', 'Gestionar despachos', 'Atender solicitudes, entregas y devoluciones.'),
        ),
    },
    {
        'label': 'Incidencias y conducta',
        'icon': 'fa-solid fa-triangle-exclamation',
        'permissions': (
            ('discipline.create', 'Registrar incidencias', 'Crear reportes disciplinarios y adjuntar evidencias.'),
            ('discipline.review', 'Revisar historial', 'Consultar y buscar reportes de incidencias.'),
        ),
    },
    {
        'label': 'Portafolio docente',
        'icon': 'fa-solid fa-folder-open',
        'permissions': (
            ('portfolio.own', 'Gestionar portafolio propio', 'Ver y subir fichas al portafolio personal.'),
            ('portfolio.review', 'Revisar portafolios', 'Consultar portafolios y registrar observaciones.'),
        ),
    },
    {
        'label': 'Documentos institucionales',
        'icon': 'fa-solid fa-file-lines',
        'permissions': (
            ('documents.view', 'Ver documentos', 'Consultar documentos permitidos para su rol.'),
            ('documents.publish', 'Publicar y editar', 'Subir y actualizar documentos institucionales.'),
            ('documents.manage', 'Administrar documentos', 'Eliminar documentos y gestionar categorías.'),
        ),
    },
)

ALL_PERMISSION_CODES = frozenset(
    code
    for group in PERMISSION_GROUPS
    for code, _label, _description in group['permissions']
)

ROLE_DEFAULT_PERMISSIONS = {
    'DIRECTOR': ALL_PERMISSION_CODES - {'warehouse.request', 'portfolio.own'},
    'SUBDIRECTOR': {
        'warehouse.view', 'warehouse.manage', 'warehouse.dispatch',
        'discipline.create', 'discipline.review', 'portfolio.review',
        'documents.view', 'documents.publish',
    },
    'APOYO': {'warehouse.view', 'warehouse.manage', 'warehouse.dispatch', 'documents.view'},
    'DOCENTE': {'documents.view'},
    'APODERADO': {'documents.view'},
}


def _legacy_permissions(user, stored_permissions):
    expanded = set()
    if 'almacen' in stored_permissions:
        expanded.add('warehouse.view')
        if user.role == 'DOCENTE':
            expanded.add('warehouse.request')
        elif user.role in {'DIRECTOR', 'SUBDIRECTOR', 'APOYO', 'SUPERUSER'}:
            expanded.update({'warehouse.manage', 'warehouse.dispatch'})
    if 'disciplina' in stored_permissions:
        expanded.update({'discipline.create', 'discipline.review'})
    if 'portafolio' in stored_permissions:
        if user.role == 'DOCENTE':
            expanded.add('portfolio.own')
        else:
            expanded.add('portfolio.review')
    return expanded


def effective_permissions(user):
    """Obtiene permisos efectivos sin romper cuentas creadas con el esquema anterior."""
    if not getattr(user, 'is_authenticated', True):
        return set()
    if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'SUPERUSER':
        return set(ALL_PERMISSION_CODES)

    stored = set(getattr(user, 'module_permissions', None) or [])
    if GRANULAR_PERMISSIONS_MARKER in stored:
        return stored & ALL_PERMISSION_CODES

    permissions = set(ROLE_DEFAULT_PERMISSIONS.get(getattr(user, 'role', None), set()))
    permissions.update(stored & ALL_PERMISSION_CODES)
    permissions.update(_legacy_permissions(user, stored))
    return permissions


def has_permission(user, permission_code):
    return permission_code in effective_permissions(user)


def permissions_for_edit(user):
    """Convierte una cuenta antigua a una lista granular explícita y editable."""
    return [GRANULAR_PERMISSIONS_MARKER, *sorted(effective_permissions(user))]


def sanitize_explicit_permissions(permission_codes):
    valid = sorted(set(permission_codes) & ALL_PERMISSION_CODES)
    return [GRANULAR_PERMISSIONS_MARKER, *valid]


def permission_groups_for(user):
    enabled = effective_permissions(user)
    return [
        {
            'label': group['label'],
            'icon': group['icon'],
            'permissions': [
                {
                    'code': code,
                    'label': label,
                    'description': description,
                    'enabled': code in enabled,
                }
                for code, label, description in group['permissions']
            ],
        }
        for group in PERMISSION_GROUPS
    ]
