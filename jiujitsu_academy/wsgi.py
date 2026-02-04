"""
WSGI config for jiujitsu_academy project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jiujitsu_academy.settings')

application = get_wsgi_application()

