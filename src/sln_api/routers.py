class SLNApiRouter:
    """
    Routes all sln_api app models to the correct database alias.

    Normal mode: routes to the 'sln_api' alias (separate DB connection).
    Admin-only mode (IS_ADMIN_ONLY=True): the 'sln_api' alias does not exist
    because 'default' IS the sln_api database, so we route to 'default'.

    Migrations for sln_api models are always blocked — the schema is owned
    by the Go API's golang-migrate system.
    """

    app_label = "sln_api"

    def _db_alias(self):
        from django.conf import settings

        return "sln_api" if "sln_api" in settings.DATABASES else "default"

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return self._db_alias()
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return self._db_alias()
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            # Go API owns this schema — never let Django touch it.
            return False
        return None
