from flask import g, abort
from app.models.tables import Organization

# python decorators are functions defined above other functions
# it will receive another function and do something with it


# this decorators verify if the user id in the arguments is the same
# as the logged in user
# if it is, it calls the original function, else the user is unauthorized
def is_user(func):
    def func_wrapper(self, id):
        if not g.user.id == id:
            abort(401)
        else:
            return func(self, id)
    return func_wrapper


# this decorators verify if the user is one of the company managers
# if it is, it calls the original function, else the user is unauthorized
def is_manager(func):
    def func_wrapper(self, id):
        org = Organization.query.get_or_404(id)
        if g.user not in org.managers:
            abort(401)
        else:
            return func(self, id)
    return func_wrapper

def is_admin(func):
    def func_wrapper(self, id):
        user = User.query.filter_by(name='admin').first()
        if not g.user.id == user.id:
            abort(401)
        else:
            return func(self, id)
    return func_wrapper
