from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission

from core.functions import api_response


class IsActiveUser(BasePermission):
    message = "Your account is deactivated."

    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated:
            if user.is_deleted:
                raise ValidationError(
                    api_response(
                        success=False,
                        message=_("Your account is deactivated."),
                        status=403
                    ).data
                )
            return True
        return False
