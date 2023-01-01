from base.settings import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DATABASE_NAME", default="vod"),
        "USER": env.str("POSTGRES_USERNAME", default="postgres"),
        "PASSWORD": env.str("POSTGRES_PASSWORD", default="postgres"),
        "HOST": env.str("DATABASE_HOST", default="127.0.0.1"),
        "PORT": env.int("DATABASE_PORT", default=5432),
        "ATOMIC_REQUESTS": True,
    }
}
