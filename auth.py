import functools
from quart import session, redirect, url_for, request


def is_logged_in(view):
    @functools.wraps(view)
    async def wrapped_view(*args, **kwargs):
        if session.get('logged_in') is None:
            return redirect(url_for('login'))

        return await view(*args, **kwargs)

    return wrapped_view
