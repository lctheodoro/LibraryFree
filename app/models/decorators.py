from flask import g, abort


def is_user(func):
    def func_wrapper(self, id):
        if not g.user.id == id:
            abort(401)
        else:
            return func(self, id)
    return func_wrapper
