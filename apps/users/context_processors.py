from apps.users.permissions import effective_permissions


def access_permissions(request):
    if not request.user.is_authenticated:
        return {'access_permissions': set()}
    return {'access_permissions': effective_permissions(request.user)}
