from rest_framework import permissions

class IsAuthenticatedOrAuthorOrReadOnly(permissions.BasePermission):
    
    def has_permission(self, request, view):
        return request.method == "GET" or request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            return request.method in ["POST", "GET"] or request.user == obj.author 
        return request.method == "GET"