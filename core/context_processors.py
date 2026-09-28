from .site import site_context


def site_info(request):
    """Expose all admin-editable chrome (settings, text, images, menus)."""
    return site_context()
