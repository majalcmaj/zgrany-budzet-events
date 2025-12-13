from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import Response, request

F = TypeVar("F", bound=Callable[..., Any])


def check_auth(username: str, password: str) -> bool:
    """Check if a username/password combination is valid."""
    return username == "mc" and password == "MiniCyfr1!"


def authenticate() -> Response:
    """Sends a 401 response that enables basic auth"""
    return Response(
        "Could not verify your access level for that URL.\n"
        "You have to login with proper credentials",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'},
    )


def auth_required(f: F) -> F:
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth = request.authorization
        if not auth or not check_auth(auth.username or "", auth.password or ""):
            return authenticate()
        return f(*args, **kwargs)

    return cast(F, decorated)
