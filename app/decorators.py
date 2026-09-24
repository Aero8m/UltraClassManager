from functools import wraps
from urllib.parse import urlparse

from flask import session, redirect, url_for, request


def _safe_next_url():
    """Return a safe redirect target to send the user back to after reauth.

    Uses the Referer header if it points to the same host; otherwise falls
    back to the dashboard.
    """
    referrer = request.referrer
    if not referrer:
        return url_for('group.dashboard')

    parsed = urlparse(referrer)
    # Only allow relative paths or same-host absolute URLs.
    if parsed.netloc and parsed.netloc != request.host:
        return url_for('group.dashboard')
    return referrer


def require_reauth(f):
    """Decorator that requires secondary authentication via password re-entry.

    When the session lacks reauth_verified, the behavior depends on the
    request type:

    - AJAX / JSON-preferring clients receive a 401 JSON response so the
      in-page modal can handle it.
    - Regular browser form submissions are redirected to the full-page
      reauth form, which then sends the user back to their original page
      after successful verification.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('reauth_verified'):
            # If the client explicitly wants JSON (the JS modal flow), return
            # 401 so the caller can show the inline reauth dialog.
            if (request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    or 'application/json' in (request.headers.get('Accept') or '')):
                return {'require_reauth': True}, 401

            # Otherwise this is a regular form POST — redirect to the
            # dedicated reauth page and bring the user back afterwards.
            return redirect(url_for(
                'auth.reauth_page', next=_safe_next_url()
            ))
        return f(*args, **kwargs)
    return decorated
