from django.db import connection
import os
import sqlite3
from django.apps import AppConfig
from django.core.management import call_command
from django.conf import settings

class InfographicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "infographic"

