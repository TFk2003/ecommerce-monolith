from rest_framework.permissions import BasePermission
 
 
class IsAdminUser(BasePermission):
    """
    Allows access only to admin users (is_staff=True).
    Replaces the raw permissions.IsAdminUser in views so we control the logic.
    """
    message = "You must be an administrator to perform this action."
 
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
 
 
class IsSellerOrAdmin(BasePermission):
    """
    Allows access to sellers (is_staff=True) or admins.
    In this repo, sellers are marked as staff. Extend if you add a separate Seller group.
    Apply to: ProductCreateView (POST/PATCH/DELETE)
    """
    message = "Only sellers or admins can manage products."
 
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
 
 
class IsAuthenticatedBuyer(BasePermission):
    """
    Allows access to any authenticated user (buyer role).
    Apply to: OrderCreateView, ReviewCreateView
    """
    message = "You must be logged in to perform this action."
 
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
 
 
class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: only the owner of an object OR an admin can access it.
    Apply to: OrderDetailView, UserDetailView
    Usage: view must set self.get_object() so has_object_permission is triggered.
    """
    message = "You do not have permission to access this resource."
 
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # obj must have a 'user' attribute (Order, ShippingAddress, etc.)
        return obj.user == request.user