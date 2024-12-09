"""
Django settings for lm_drive_API project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from decouple import config

# Load environment variables from .env file
load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# General Settings
SECRET_KEY = config("SECRET_KEY", default="changeme")
DEBUG = config("DEBUG", default="False", cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ROOT_URLCONF = config("ROOT_URLCONF", default="lm_drive_API.urls")

# Static & Media Files
STATIC_URL = "/python/static/"
STATIC_ROOT = "/usr/local/lsws/Example/html/lm_dive_api/lm_drive_API/public/static"

MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Installed Applications
INSTALLED_APPS = [
    # Default Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    # Project-specific apps
    "authentication",
    "store",
    "orders",
    "payments",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI Configuration
WSGI_APPLICATION = "lm_drive_API.wsgi.application"

# Database Configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DATABASE_NAME", default="default_db_name"),
        "USER": config("DATABASE_USER", default="root"),
        "PASSWORD": config("DATABASE_PASSWORD", default=""),
        "HOST": config("DATABASE_HOST", default="localhost"),
        "PORT": config("DATABASE_PORT", default="3306"),
    }
}

# Authentication & Authorization
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# REST Framework Settings
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
}

# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": config("JWT_SIGNING_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# CORS Configuration
CORS_ORIGIN_ALLOW_ALL = config("CORS_ORIGIN_ALLOW_ALL", default=False, cast=bool)
CORS_ORIGIN_WHITELIST = config(
    "CORS_ORIGIN_WHITELIST", default="http://127.0.0.1:5173"
).split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-requested-with",
]

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY")
STRIPE_TEST_SECRET_KEY = config("STRIPE_TEST_SECRET_KEY")
STRIPE_RETURN_URL = config("STRIPE_RETURN_URL", default="http://localhost:5173/")
