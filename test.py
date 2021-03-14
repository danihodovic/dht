# import os
# # from django.conf import settings
# # from django.apps import apps
#
# conf = {
#     'INSTALLED_APPS': [
#         'demo'
#     ],
#     'DATABASES': {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': os.path.join('.', 'db.sqlite3'),
#         }
#     },
#     'SECRET_KEY': 'very_secret',
# }
#
# # settings.configure(**conf)
# # apps.populate(settings.INSTALLED_APPS)
import os

from django.apps import apps
from django.conf import settings
from django.core.management import execute_from_command_line

# Django settings
settings.configure(
    DEBUG=False,
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "db.sqlite3",
            "USER": "",
            "PASSWORD": "",
            "HOST": "",
            "PORT": "",
        }
    },
    INSTALLED_APPS=[
        "demo",
    ],
)

apps.populate(settings.INSTALLED_APPS)
execute_from_command_line(["manage.py", "makemigrations"])
execute_from_command_line(["manage.py", "migrate"])

from demo.models import Foo

Foo.objects.get_or_create(name="Dani")
print(Foo.objects.get(name="Dani"))
