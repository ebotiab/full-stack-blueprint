"""Sign-in through an external OpenID Connect provider (Auth0, Keycloak, Zitadel, Logto, Neon Auth…).

The provider owns the accounts and issues signed JWTs; clients send them as
`Authorization: Bearer <token>`, and this package only verifies them (`verify.py`) against the
provider's published keys. A route requires a signed-in caller with a `CurrentUser` parameter
from `deps.py`. Settings: `AUTH_ISSUER` and the others in `settings.py`.

Invariants (tests/test_auth.py checks each one):

- Only asymmetric signatures are accepted (RS256, ES256, EdDSA): an HS256 token signed with the
  provider's public key is refused.
- Issuer and expiry are always required. Shared issuers need the API's audience. A dedicated
  issuer may use tokens without an audience when the allowed authorized parties are configured.
- When configured together, the token must match both audience and authorized party.
- The keys are cached: an unknown key id fetches them again, at most once a minute.
"""
