class FlaskApp(object):
    _current_app = None

    @classmethod
    def current(cls):
        if not cls._current_app:
            raise Exception("FlaskApp not initialized.")
        return cls._current_app

    @classmethod
    def app_context(cls):
        return cls.current().app_context()

    @classmethod
    def set(cls, app):
        if cls._current_app != None:
            raise Exception("FlaskApp already exists.")
        cls._current_app = app

    @classmethod
    def cleanup(cls):
        cls._current_app = None
