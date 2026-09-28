from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("packages/", views.packages, name="packages"),
    path("packages/<slug:slug>/", views.package_detail, name="package_detail"),
    path("gallery/", views.gallery, name="gallery"),
    path("about/", views.about, name="about"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),

    # JSON API used by the front-end
    path("api/packages/<slug:slug>/", views.package_detail_json, name="package_detail_json"),
    path("api/inquiry/", views.inquiry_create, name="inquiry_create"),

    path("dashboard/", include("core.dashboard.urls")),
]
