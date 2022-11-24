"""
Predefined authenticators for popular services.
"""

from loctocat.auth import Authenticator

__all__ = ["GitHubAuthenticator"]


class GitHubAuthenticator(Authenticator):
    """
    Authenticate users with GitHub.

    Parameters
    ----------
    client_id : str
        Your GitHub OAuth app's client ID.
    scopes : list[str], optional
        The scopes to request.
    """

    def __init__(self, client_id: str, scopes: list[str] = None):
        self.client_id = client_id
        self.scope = scopes

        auth_url = "https://github.com/login/device/code"
        token_url = "https://github.com/login/oauth/access_token"

        super().__init__(client_id, auth_url, token_url, scopes)
