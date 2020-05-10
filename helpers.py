import re

from flask import redirect, session
from functools import wraps


# email validation
def validate_email(email):

    # regular expression for email validation
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'

    if(re.search(regex,email)):
        return True
    else:
        False


# Decorate routes to require login.
def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function
