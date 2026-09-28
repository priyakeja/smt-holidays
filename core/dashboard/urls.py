from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", views.DashboardLoginView.as_view(), name="login"),
    path("logout/", views.DashboardLogoutView.as_view(), name="logout"),

    # Fixed pages first so the generic <slug> routes never swallow them.
    path("", views.index, name="index"),
    path("content/text/", views.text_blocks, name="text_blocks"),
    path("content/images/", views.images, name="images"),
    path("settings/", views.settings_view, name="settings"),
    path("media/", views.media_library, name="media"),
    path("inbox/<int:pk>/", views.inquiry_detail, name="inquiry_detail"),

    # Generic CRUD driven by core/dashboard/registry.py
    path("<slug:slug>/", views.resource_list, name="resource_list"),
    path("<slug:slug>/new/", views.resource_form, name="resource_create"),
    path("<slug:slug>/export/", views.resource_export, name="resource_export"),
    path("<slug:slug>/<int:pk>/", views.resource_form, name="resource_update"),
    path("<slug:slug>/<int:pk>/delete/", views.resource_delete, name="resource_delete"),
    path("<slug:slug>/<int:pk>/toggle/", views.resource_toggle, name="resource_toggle"),
    path("<slug:slug>/<int:pk>/move/", views.resource_move, name="resource_move"),
]
