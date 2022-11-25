# loctocat

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/loctocat?logo=pypi&logoColor=white&style=for-the-badge)](https://pypi.org/project/loctocat)
[![PyPI](https://img.shields.io/pypi/v/loctocat?color=green&logo=pypi&style=for-the-badge&logoColor=white)](https://pypi.org/project/loctocat)
[![GitHub release (latest SemVer including pre-releases)](https://img.shields.io/github/v/release/celsiusnarhwal/loctocat?color=orange&include_prereleases&label=latest%20release&logo=github&style=for-the-badge)](https://github.com/celsiusnarhwal/loctocat/releases/latest)
[![PyPI - License](https://img.shields.io/pypi/l/loctocat?color=03cb98&style=for-the-badge)](https://github.com/celsiusnarhwal/loctocat/blob/HEAD/LICENSE.md)

loctocat brings simple yet flexible OAuth 2.0 device flow authentication to Python. It has built-in asyncio support
and even predefined authenticators for popular services. Plus, it's fully compliant with
[RFC 8628](https://tools.ietf.org/html/rfc8628), making it compatible with any OAuth2-supporting service that
(correctly) implements the standard.

## Installation

```bash
pip install loctocat
```

## Basic Usage

### The `Authenticator` Class

Every authentication flow starts with loctocat's `Authenticator` class.

```python
from loctocat import Authenticator

authenticator = Authenticator(
    client_id="your_client_id",
    auth_url="https://example.com/oauth2/authorize",
    token_url="https://example.com/oauth2/token",
    scopes=["list", "of", "scopes"],
)
```

It's pretty simple — just instantiate the class with your client ID, authorization URL (where you'll get your device
and user codes), token URL (where you'll poll the authorization server for an access token), and a list of any scopes
you need.

Once you've got an `Authenticator`, getting an access token is as simple as:

```python
token = authenticator.authenticate()
```

Whoa. That was easy.

`Authenticator.authenticate()` will, in order:

1. Obtain device and user codes from the authorization server
2. Prompt the user to visit the verficiation URL and enter the user code
3. Poll the authorization server for an access token
4. Return the access token as a string

Here's an example of using `Authenticator` to authenticate with GitHub:

```python
# https://docs.github.com/en/developers/apps/building-oauth-apps/authorizing-oauth-apps#device-flow

from loctocat import Authenticator

authenticator = Authenticator(
    client_id="github_client_id",  # Replace this with your app's actual client ID, obviously.
    auth_url="https://github.com/login/device/code",
    token_url="https://github.com/login/oauth/access_token",
    scopes=["repo"],  # https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps
)

token = authenticator.authenticate()
```

Like I said, easy. Unless you're building an asynchronous application, in which case this doesn't work at all, since
`Authenticator.authenticate()` is a blocking call. Fortunately, loctocat has you covered.

### The `AsyncAuthenticator` Class

`AsyncAuthenticator` is a subclass of `Authenticator` that functions exactly the same except all its methods are
asynchronous (and therefore must be called with `await`). Here's an example of `AsyncAuthenticator` in action:

```python
from loctocat import AsyncAuthenticator

authenticator = AsyncAuthenticator(
    client_id="your_client_id",
    auth_url="https://example.com/oauth2/authorize",
    token_url="https://example.com/oauth2/token",
    scopes=["list", "of", "scopes"],
)

token = await authenticator.authenticate()
```

Whoa. That was easy.

`AsyncAuthenticator.authenticate()` will, in or—wait, I'm getting déjà vu.

## Advanced Usage

Maybe `Authenticator.authenticate()` is too simplistic for you. Maybe you'd rather, I don't know,
handle the user-facing authentication prompt yourself, or control when loctocat starts polling for access tokens.
Fortunately, locotcat has you covered.

(Keep in mind that `AsyncAuthenticator` is a subclass of `Authenticator` and inherits all of its methods and
attributes.)

### `Authenticator.ping()`

`Authenticator.ping()` requests device and user codes from the authorization server, returning a `LoctocatAuthInfo`
object that looks like this:

```py
class LoctocatAuthInfo:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int
```

Pretty self-explanatory. You can do whatever you want with this information (aside from change it
— `LoctocatAuthInfo`'s attributes are read-only). For example, you could prompt the user with some custom text
containing the user code and verification URI:

```python
auth_info = authenticator.ping()

print(f"Check it out, yo! This is some epic text telling YOU to go {auth_info.verification_uri} and enter {auth_info.user_code}! Swag!")
```

### `Authenticator.poll()`

`Authenticator.poll()` polls the authorization server for an access token, returning it as a string. You **don't**
need to pass the `LoctocatAuthInfo` object returned by `Authenticator.ping()` to `Authenticator.poll()` — the
authorization info is automatically remembered by `Authenticator`. All you have to do is call the method:

```python
# Authenticator.ping() must have been called on the Authenticator object already or this will not work.

token = authenticator.poll()
```

Whoa. That was easy.

(Fun fact: `Authenticator.authenticate()` is just a wrapper around `ping()` and `poll()`.)

## Pro Usage

Maybe [Advanced Usage](#advanced-usage) isn't advanced enough for you. Maybe you're working with an authorization
server that requires parameters beyond those defined by `Authenticator`. Maybe you want to customize the prompts and
messages displayed by `Authenticator.authenticate()` without having to use `Authenticator.ping()` and
`Authenticator.poll()`. Maybe loctocat has a predefined authenticator for a service you like, and you want to use it.
Unfortunately, loctocat doesn't have you covered.

...

Okay, loctocat actually does have you covered, but that stuff is the domain of loctocat's unfinished documentation
site. Emphasis on unfinished. It's not finished yet.

Fortunately, loctocat has you covered. loctocat's a pretty small library and it's public modules and classes are all
properly documented in the source code, so you're welcome to learn by example(?) and take a look around.

Or you could wait until I finish the documentation site. I'm not your mother.

## FAQ

Maybe you have questions about loctocat that haven't been answered by the rest of this README. Maybe you just want to see me talk to
myself for like, two paragraphs. Fortunately, loctocat has you covered.

### Q: loctowhat now

A: Lock + [Octocat](https://octodex.github.com). loctocat was born out of my need for a Python library that implemented
OAuth 2.0 device flow authentication for GitHub.

### Q: pretty sure I can do this with requests-oauthlib or [INSERT OAUTH LIBRARY HERE] just fine dude

A: Sure you can. In fact, loctocat uses requests and oauthlib under the hood. So let's leave loctocat behind and
write a function to authenticate with GitHub using requests and oauthlib, together!

```python
import time

import requests
from oauthlib.oauth2 import DeviceClient

def authenticate_with_github(client_id: str, scopes: list[str]) -> str:
    auth_url = "https://github.com/login/device/code"
    token_url = "https://github.com/login/oauth/access_token"
    client = DeviceClient(client_id=client_id, scope=scopes)
    
    uri = client.prepare_request_uri(auth_url)
    response = requests.post(uri, headers={"Accept": "application/json"}).json()
    
    uri = client.prepare_request_uri(token_url, code=response["device_code"])
    
    while True:
        response = requests.post(uri, headers={"Accept": "application/json"}).json()
        
        if "error" in response:
            if response["error"] == "authorization_pending":
                time.sleep(response["interval"])
                continue
            elif response["error"] == "slow_down":
                time.sleep(response["interval"])
                continue
            else:
                raise RuntimeError(response["error"])
        else:
            return response["access_token"]
```

Damn, that plate can boil!

Now let's do the same thing, but with loctocat.

```python
from loctocat.predefined import GitHubAuthenticator

def authenticate_with_github(client_id: str, scopes: list[str]) -> str:
    authenticator = GitHubAuthenticator(client_id=client_id, scopes=scopes)
    return authenticator.authenticate()

# "Hey, that's cheating!" Fine, let's do it the hard way.

from loctocat import Authenticator

def authenticate_with_github(client_id: str, scopes: list[str]) -> str:
    authenticator = Authenticator(
        client_id=client_id,
        auth_url="https://github.com/login/device/code",
        token_url="https://github.com/login/oauth/access_token",
        scopes=scopes
    )
    
    return authenticator.authenticate()
```

Whoa. That was easy.

Part of the reason I made loctocat is that no other library capable of doing what loctocat does did it in a way that
didn't SUCK. The first example SUCKS. The second example is AWESOME. Case closed.


### Q: loctocat isn't working with [INSERT SERVICE HERE] and I'm FRUSTRATED AAAAGGGGGGHHHHH

A: loctocat is compliant with the OAuth 2.0 Device Authorization Grant standard so it's probably the service's fault.
Make sure the service actually does support the device flow and is generally compliant with RFC 8628. If you're sure
loctocat is the problem, [open an issue](https://github.com/celsiusnarhwal/loctocat/issues/new).

### Q: oh my god thank you I've been looking for a library like this forever you have no idea

A: You're very welcome. 🙂

## License

In an age where developers must take great caution not to tread on the intellectual property of others, you must be
hoping that a such an incredible library is made available under a permissive license. Fortunately,
loctocat has you covered.

loctocat is licensed under the [MIT License](https://github.com/celsiusnarhwal/loctocat/blob/HEAD/LICENSE.md).
