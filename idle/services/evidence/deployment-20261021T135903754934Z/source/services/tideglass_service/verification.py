"""Trust boundaries: clients submit proofs, never trusted purchase/ad states.

No permissive or fixture verifier is shipped. Real store/provider implementations
must verify application, environment, account binding, product, transaction and
revocation ordering before returning one of these internal observations.
"""
from dataclasses import dataclass
from typing import Protocol


class VerificationUnavailable(Exception):
    pass


@dataclass(frozen=True)
class PurchaseObservation:
    platform: str
    transaction_id: str
    account_id: str
    product_id: str
    state: str  # pending, purchased, revoked
    version: int  # provider-monotonic observation ordering, not client time
    authority: str


@dataclass(frozen=True)
class AdObservation:
    transaction_id: str
    account_id: str
    day_id: int
    slot: int
    authority: str


class PurchaseVerifier(Protocol):
    def verify(self, platform: str, proof: str, account_id: str) -> PurchaseObservation: ...
    def acknowledge(self, observation: PurchaseObservation) -> None: ...


class AdVerifier(Protocol):
    def verify(self, proof: str, account_id: str, day_id: int, slot: int) -> AdObservation: ...


class UnconfiguredPurchaseVerifier:
    def verify(self, platform, proof, account_id):
        raise VerificationUnavailable('Store verification is not configured.')

    def acknowledge(self, observation):
        raise VerificationUnavailable('Store acknowledgement is not configured.')


class UnconfiguredAdVerifier:
    def verify(self, proof, account_id, day_id, slot):
        raise VerificationUnavailable('Rewarded-ad verification is not configured.')


PRODUCTS = {
    **{f'dev.tideglass.cosmetic.{i:02d}': [f'cosmetic.shop.{i:02d}'] for i in range(1, 5)},
    'dev.tideglass.pass.01': ['pass.01'],
    'dev.tideglass.supporter': [*[f'cosmetic.shop.{i:02d}' for i in range(1, 5)], 'soundtrack.01'],
}
