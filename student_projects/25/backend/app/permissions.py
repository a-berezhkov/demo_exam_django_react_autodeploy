from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsTeacherOrAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            return request.user.role == 'teacher' or request.user.is_staff

        return  False

