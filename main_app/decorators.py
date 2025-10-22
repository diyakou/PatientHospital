# main_app/decorators.py

from django.core.exceptions import PermissionDenied

def nurse_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'nurse'):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap
