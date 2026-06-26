"""Test's settings"""

import os
import tempfile

import django
from django.utils.translation import gettext_noop

DEBUG = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

SECRET_KEY = "NOTASECRET"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    # modeltranslation must be declared before django.contrib.admin
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "easy_thumbnails",
    "easy_thumbnails.optimize",
    "filer",
    "filer_optimizer",
    "ordered_model",
    "taggit",
    "hashtag",
    "django_prose_editor",
    "services",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ],
        },
    }
]

ROOT_URLCONF = "tests.urls"

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

USE_TZ = True
LANGUAGE_CODE = "en"
USE_I18N = True

STATIC_URL = "/static/"

MEDIA_URL = "/media/"
MEDIA_ROOT = tempfile.mkdtemp(prefix="django-service-tests-")

# Languages we provide translations for, out of the box.
LANGUAGES = [
    ("de", gettext_noop("German")),
    ("en", gettext_noop("English")),
    ("es", gettext_noop("Spanish")),
    ("fr", gettext_noop("French")),
    ("it", gettext_noop("Italian")),
    ("ja", gettext_noop("Japanese")),
    ("nl", gettext_noop("Dutch")),
    ("ru", gettext_noop("Russian")),
    ("zh-hans", gettext_noop("Simplified Chinese")),
    ("zh-hant", gettext_noop("Traditional Chinese")),
]

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"

if django.VERSION < (4, 2):
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE
else:
    # See: https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-STORAGES
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    THUMBNAIL_DEFAULT_STORAGE = STORAGES["default"]["BACKEND"]

# THUMBNAIL
FILER_STORAGES = {
    "public": {
        "thumbnails": {
            "THUMBNAIL_OPTIONS": {"base_dir": ""},
        },
    },
}

THUMBNAIL_PREFIX = ""

# Aliases consumed by filer_optimizer.annotate_queryset_with_thumbnails for the
# "head", "preview" and "grid" sizes referenced by the services views.
THUMBNAIL_ALIASES = {
    "default": {
        "head": {"size": (1200, 600), "crop": True},
        "preview": {"size": (600, 400), "crop": True},
        "grid": {"size": (300, 200), "crop": True},
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
