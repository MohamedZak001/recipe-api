"""
Django command to wait for the database to be ready to be connected
"""
from typing import Any
import time
from psycopg2 import OperationalError as Psycopg2Error
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for db"""

    def handle(self, *args: Any, **options: Any):
        db_available = False

        while db_available is False:
            try:
                self.check(databases=["default"])
                db_available = True

            except (Psycopg2Error, OperationalError):
                self.stdout.write("Database is unavailable ")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database is available "))
