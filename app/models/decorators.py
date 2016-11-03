from flask import g, abort
from app.models.tables import Organization


def is_user(func):
    def func_wrapper(self, id):
        if not g.user.id == id:
            abort(401)
        else:
            return func(self, id)
    return func_wrapper


def is_manager(func):
    def func_wrapper(self, id):
        org = Organization.query.get_or_404(id)
        if g.user not in org.managers:
            abort(401)
        else:
            return func(self, id)
    return func_wrapper
