"""Verification of the provider's tokens: JWTs signed with keys from its JWKS.

The keys are fetched with the project's async httpx (not PyJWT's `PyJWKClient`, which blocks),
kept for an hour, and fetched again when a token names a key id the cache does not have (the
provider rotated its keys), but never more than once a minute: tokens with made-up key ids cannot
make this API flood the provider.
"""

import asyncio
import time
from collections.abc import Callable, Sequence
from typing import Any

import httpx
import jwt

from ..settings import PREFIX

CACHE_SECONDS = 3600.0
REFETCH_SECONDS = 60.0
#: Clock difference tolerated between the provider and this server, for `exp` and `nbf`.
LEEWAY_SECONDS = 30


class InvalidToken(Exception):
    """A token this API does not accept; the message says why."""


class ProviderUnavailable(Exception):
    """The provider's keys could not be fetched and none are cached."""


class Verifier:
    def __init__(
        self,
        issuer: str,
        *,
        algorithms: Sequence[str],
        jwks_url: str | None = None,
        audience: str | None = None,
        authorized_parties: Sequence[str] = (),
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not issuer or not (audience or authorized_parties):
            raise ValueError(
                f"Set {PREFIX}AUTH_ISSUER and {PREFIX}AUTH_AUDIENCE. For a dedicated issuer "
                f"with no audience claim, set {PREFIX}AUTH_AUTHORIZED_PARTIES and the issuer."
            )
        self.issuer = issuer
        self.algorithms = list(algorithms)
        self.jwks_url = jwks_url
        self.audience = audience
        self.authorized_parties = list(authorized_parties)
        self._transport = transport
        self._clock = clock
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at: float | None = None
        self._lock = asyncio.Lock()

    async def claims(self, token: str) -> dict[str, Any]:
        """The token's claims, once its signature, issuer, expiry and audience are checked."""
        try:
            header = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as error:
            raise InvalidToken(str(error)) from None
        key = await self._key(str(header.get("kid", "")))
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=self.algorithms,
                issuer=self.issuer,
                audience=self.audience,
                leeway=LEEWAY_SECONDS,
                options={"require": ["exp", "iss", "sub"], "verify_aud": self.audience is not None},
            )
        except jwt.InvalidTokenError as error:
            raise InvalidToken(str(error)) from None
        if self.audience is None and "aud" in claims:
            raise InvalidToken("This token names an audience, but the API has none configured.")
        if self.authorized_parties and claims.get("azp") not in self.authorized_parties:
            raise InvalidToken("The token was issued to another client (azp).")
        return claims

    async def _key(self, kid: str) -> jwt.PyJWK:
        if kid not in self._keys or self._stale():
            async with self._lock:
                fetched = self._fetched_at
                may_fetch = fetched is None or self._clock() - fetched >= REFETCH_SECONDS
                if (kid not in self._keys or self._stale()) and may_fetch:
                    await self._fetch()
        if not self._keys:
            raise ProviderUnavailable("No signing keys from the provider yet.")
        key = self._keys.get(kid)
        if key is None:
            raise InvalidToken(f"No signing key with id {kid!r}.")
        return key

    def _stale(self) -> bool:
        return self._fetched_at is None or self._clock() - self._fetched_at >= CACHE_SECONDS

    async def _fetch(self) -> None:
        try:
            async with httpx.AsyncClient(transport=self._transport, timeout=10) as client:
                if self.jwks_url is None:
                    discovery = f"{self.issuer.rstrip('/')}/.well-known/openid-configuration"
                    self.jwks_url = (await _get_json(client, discovery))["jwks_uri"]
                jwks = await _get_json(client, self.jwks_url)
        except (httpx.HTTPError, ValueError, KeyError) as error:
            # Keep the keys we have; try again at the next refetch.
            self._fetched_at = self._clock()
            if not self._keys:
                raise ProviderUnavailable(f"Could not fetch the provider's keys: {error}") from None
            return
        keys: dict[str, jwt.PyJWK] = {}
        for data in jwks.get("keys", []):
            if "kid" not in data or data.get("use", "sig") != "sig":
                continue
            try:
                keys[data["kid"]] = jwt.PyJWK(data)
            except jwt.PyJWKError:
                continue  # a key type this API does not use
        self._keys = keys
        self._fetched_at = self._clock()


async def _get_json(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    response = await client.get(url)
    response.raise_for_status()
    return response.json()
