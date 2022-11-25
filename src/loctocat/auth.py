"""
Core classes for OAuth 2.0 device flow authentication.
"""

from __future__ import annotations

import time
from typing import Callable

import aiohttp
import requests
from halo import Halo
from oauthlib.oauth2 import DeviceClient
from termcolor import colored

from loctocat._spinner import _Spinner
from loctocat.exceptions import *

__all__ = ["Authenticator", "AsyncAuthenticator", "Handler", "LoctocatAuthInfo"]


class Handler:
    """
    A handler for an error code returned by an authorization server.

    Parameters
    ----------
    error: str
        The error code returned by the authorization server.
    action: Callable[[Authenticator], None]
        The function to be called when the error code is returned. The function
        must take an class:`Authenticator` object as its only parameter.
    continue_on_error: bool, optional
        Whether to continue the authentication process after the handler is
        called. Defaults to True.
    """

    def __init__(self, error: str, action: Callable[[Authenticator], None], continue_on_error: bool = True):
        self.error = error
        self.action = action
        self.continue_on_error = continue_on_error


class LoctocatAuthInfo:
    """
    A set of information returned by an authorization server.

    Parameters
    ----------
    device_code: str
        The device code.
    user_code: str
        The user code. This is the code the user must use to authorize your app.
    verificiation_uri: str
        The URL the user must visit to authorize your app.
    expires_in: int
        The number of seconds for which the device code is valid.
    interval: int
        The minimum number of seconds your app must wait between polling requests.
    """
    __slots__ = ["device_code", "user_code", "verification_uri", "expires_in", "interval"]

    def __init__(self, device_code, user_code, verificiation_uri, expires_in, interval):
        self.device_code = device_code
        self.user_code = user_code
        self.verification_uri = verificiation_uri
        self.expires_in = expires_in
        self.interval = interval


class Authenticator:
    """
    A class for authenticating with OAuth 2.0 APIs using the device flow.

    Parameters
    ----------
    client_id: str
        Your app's client ID.
    client_secret: str
        Your app's client secret.
    auth_url: str
        The URL from which your app will request device and user codes.
    token_url: str
        The URL which your app with poll for an authorization token.
    scopes: list[str], optional
        A list of scopes your app will request access to. Defaults to None.
    poll_interval: int, optional
        The number of seconds your app will wait between polling requests. Defaults to 5.
    extras: keyword arguments, optional
        Any additional parameters required by the authorization server.
    """

    def __init__(self, client_id: str, auth_url: str, token_url: str, scopes: list[str] = None, poll_interval: int = 5,
                 **extras):
        self.client_id = client_id
        self.auth_url = auth_url
        self.token_url = token_url
        self.scopes = scopes
        self.poll_interval = poll_interval

        self.auth_info: LoctocatAuthInfo = None

        self._handlers = []
        self._dc = DeviceClient(client_id=self.client_id, scope=self.scopes, **extras)

        for handler in self._get_default_handlers():
            self.attach_handler(handler)

    def authenticate(self,
                     use_default_message: bool = True, message: str = None,
                     use_default_success_message: bool = True, success_message: str = None,
                     use_default_spinner: bool = True, spinner: Halo = None) -> str:
        """
        Authenticate with the authorization server.

        Parameters
        ----------
        use_default_message: bool, optional
            Whether to use the default message. See the message parameter. Defaults to True.
        message: str, optional
            The message to display to the user when requesting authorization. Defaults to None. If a truthy value is
            provided, it will override the default message even if use_default_message is True.
        use_default_success_message: bool, optional
            Whether to use the default success message. See the success_message parameter. Defaults to True.
        success_message: str, optional
            The message to display to the user upon successful authentication. Defaults to None. If a truthy value is
            provided, it will override the default success message even if use_default_success_message is True.
        use_default_spinner: bool, optional
            Whether to use the default spinner. See the spinner parameter. Defaults to True.
        spinner: Halo, optional
            The Halo spinner to display while waiting for the user to authorize your app. Defaults to None. If a truthy
            value is provided, it will override the default spinner even if use_default_spinner is True.

        Returns
        -------
        str
            The access token returned by the authorization server.
        """
        self.ping()

        if use_default_message and not message:
            print(f"Go to {self.auth_info.verification_uri} and enter code "
                  f"{colored(self.auth_info.user_code, attrs=['bold'])} to authenticate.")
        elif message:
            print(message)

        if use_default_spinner and not spinner:
            spinner = Halo(text="Waiting for authentication...", spinner="dots")

        with _Spinner(spinner) as sp:
            token = self.poll()

            if use_default_success_message and not success_message:
                sp.succeed("Authentication successful!")
            elif success_message:
                sp.succeed(success_message)
            else:
                sp.succeed()

            return token

    def ping(self) -> LoctocatAuthInfo:
        """
        Request device and user codes from the authorization server.

        Returns
        -------
        LoctocatAuthInfo
            A LocotocatAuthInfo object containing the information returned by the authorization server.
        """
        uri = self._dc.prepare_request_uri(self.auth_url)
        response = requests.post(uri, headers={"Accept": "application/json"}).json()

        auth_info = LoctocatAuthInfo(
            device_code=response["device_code"],
            user_code=response["user_code"],
            verificiation_uri=response.get("verification_uri") or response.get("verification_url"),
            expires_in=response["expires_in"],
            interval=response["interval"],
        )

        self.auth_info = auth_info

        return auth_info

    def poll(self) -> str:
        """
        Poll the authorization server for an access token.

        Returns
        -------
        str
            The access token returned by the authorization server.
        """
        uri = self._dc.prepare_request_uri(self.token_url, device_code=self.auth_info.device_code)

        while True:
            response = requests.post(uri, headers={"Accept": "application/json"}).json()

            if "error" in response:
                handler: Handler = next((h for h in self._handlers if h.error == response["error"]), None)
                if handler:
                    handler.action(self)
                    if handler.continue_on_error:
                        continue
                    else:
                        break
                else:
                    raise ServerError(response['error'])
            else:
                return response["access_token"]

    def attach_handler(self, handler: Handler):
        """
        Attach a handler to the Authenticator. If you attach a handler for an error for which a handler already exists,
        the existing handler will be overwritten.

        Parameters
        ----------
        handler: Handler
            The handler to attach.
        """
        try:
            self._handlers.remove(next(h for h in self._handlers if h.error == handler.error))
        except StopIteration:
            pass

        self._handlers.append(handler)

    def get_handlers(self) -> list[Handler]:
        """
        Return a list of all handlers currently attached to the Authenticator.

        Returns
        -------
        list[Handler]
            A list of all handlers currently attached to the Authenticator.
        """
        return self._handlers

    @staticmethod
    def _get_default_handlers():
        return [
            Handler("authorization_pending", lambda ctx: time.sleep(ctx.auth_info.interval)),
            Handler("slow_down", lambda ctx: ctx.poll_interval == ctx.poll_interval + 5),
        ]


class AsyncAuthenticator(Authenticator):
    """
    A class for asynchronously authenticating with OAuth 2.0 APIs using the device flow.
    """

    async def authenticate(self,
                           use_default_message: bool = True, message: str = None,
                           use_default_success_message: bool = True, success_message: str = None,
                           use_default_spinner: bool = True, spinner: Halo = None) -> str:
        """
        Authenticate with the authorization server.

        Parameters
        ----------
        use_default_message: bool, optional
            Whether to use the default message. See the message parameter. Defaults to True.
        message: str, optional
            The message to display to the user when requesting authorization. Defaults to None. If a truthy value is
            provided, it will override the default message even if use_default_message is True.
        use_default_success_message: bool, optional
            Whether to use the default success message. See the success_message parameter. Defaults to True.
        success_message: str, optional
            The message to display to the user upon succesful authentication. Defaults to None. If a truthy value is
            provided, it will override the default success message even if use_default_success_message is True.
        use_default_spinner: bool, optional
            Whether to use the default spinner. See the spinner parameter. Defaults to True.
        spinner: Halo, optional
            The Halo spinner to display while waiting for the user to authorize your app. Defaults to None. If a truthy
            value is provided, it will override the default spinner even if use_default_spinner is True.

        Returns
        -------
        str
            The access token returned by the authorization server.
        """
        await self.ping()

        if use_default_message and not message:
            print(f"Go to {self.auth_info.verification_uri} and enter code "
                  f"{colored(self.auth_info.user_code, attrs=['bold'])} to authenticate.")
        elif message:
            print(message)

        if use_default_spinner and not spinner:
            spinner = Halo(text="Waiting for authentication...", spinner="dots")

        with _Spinner(spinner) as sp:
            token = await self.poll()

            if use_default_success_message and not success_message:
                sp.succeed("Authentication successful!")
            elif success_message:
                sp.succeed(success_message)
            else:
                sp.succeed()

            return token

    async def ping(self) -> LoctocatAuthInfo:
        """
        Request device and user codes from the authorization server.

        Returns
        -------
        LoctocatAuthInfo
            A LocotocatAuthInfo object containing the information returned by the authorization server.
        """
        uri = self._dc.prepare_request_uri(self.auth_url)

        async with aiohttp.ClientSession() as session:
            async with session.post(uri, headers={"Accept": "application/json"}) as response:
                response = await response.json()

        auth_info = LoctocatAuthInfo(
            device_code=response["device_code"],
            user_code=response["user_code"],
            verificiation_uri=response.get("verification_uri") or response.get("verification_url"),
            expires_in=response["expires_in"],
            interval=response["interval"],
        )

        self.auth_info = auth_info

        return auth_info

    async def poll(self) -> str:
        """
        Poll the authorization server for an access token.

        Returns
        -------
        str
            The access token returned by the authorization server.
        """
        uri = self._dc.prepare_request_uri(self.token_url, device_code=self.auth_info.device_code)

        while True:
            async with aiohttp.ClientSession() as session:
                async with session.post(uri, headers={"Accept": "application/json"}) as response:
                    response = await response.json()

            if "error" in response:
                handler: Handler = next((h for h in self._handlers if h.error == response["error"]), None)
                if handler:
                    handler.action(self)
                else:
                    raise ServerError(f"The server returned the following error: {response['error']}")
            else:
                return response["access_token"]
