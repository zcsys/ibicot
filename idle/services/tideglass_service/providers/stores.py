"""Real authenticated Apple/Google verification. No credentials are bundled.

Provider response doubles belong only in tests; default constructors use the
actual official Apple SDK and google-auth HTTPS transport. Products are fixed
non-consumables, not subscriptions, consumable currency or rental offers.
"""
import hashlib
import json
import re
from urllib.parse import quote
from ..verification import PurchaseObservation, VerificationUnavailable, PRODUCTS


def proof_json(proof, fields):
    try:
        value=json.loads(proof)
        if not isinstance(value,dict) or set(value)!=set(fields):raise ValueError()
        if not all(isinstance(value[k],str) and 0<len(value[k])<=65536 for k in fields):raise ValueError()
        if value.get('expected_product_id') not in PRODUCTS:raise ValueError()
        return value
    except (ValueError,TypeError):raise VerificationUnavailable('Invalid provider proof.') from None


class ApplePurchaseVerifier:
    def __init__(self, *, signing_key:bytes, key_id:str, issuer_id:str, bundle_id:str,
                 root_certificates:list[bytes], environment:str, app_apple_id:int|None=None):
        from appstoreserverlibrary.api_client import AppStoreServerAPIClient
        from appstoreserverlibrary.models.Environment import Environment
        from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier
        if environment not in {'Sandbox','Production'} or not root_certificates or not all((signing_key,key_id,issuer_id,bundle_id)):
            raise ValueError('Explicit Apple signing identity, root certificates and environment required.')
        self.environment=environment;self.bundle_id=bundle_id
        env=Environment(environment)
        self.client=AppStoreServerAPIClient(signing_key,key_id,issuer_id,bundle_id,env)
        self.verifier=SignedDataVerifier(root_certificates,True,env,bundle_id,app_apple_id)

    def verify(self,platform,proof,account_id):
        if platform!='apple':raise VerificationUnavailable('Wrong provider.')
        value=proof_json(proof,{'transaction_id','expected_product_id'})
        if not re.fullmatch(r'[0-9]{1,40}',value['transaction_id']):raise VerificationUnavailable('Invalid Apple transaction identity.')
        try:
            # Fetch a fresh provider view: an old client-supplied signed JWS
            # cannot hide a refund that occurred after its signature date.
            response=self.client.get_transaction_info(value['transaction_id'])
            decoded=self.verifier.verify_and_decode_signed_transaction(response.signedTransactionInfo)
            if (decoded.transactionId!=value['transaction_id'] or decoded.productId!=value['expected_product_id'] or
                decoded.bundleId!=self.bundle_id or str(decoded.appAccountToken).lower()!=account_id.lower() or
                decoded.rawEnvironment!=self.environment or decoded.quantity!=1 or decoded.rawType!='Non-Consumable' or
                type(decoded.signedDate) is not int or decoded.signedDate<0):
                raise VerificationUnavailable('Apple transaction binding mismatch.')
            state='revoked' if decoded.revocationDate is not None else 'purchased'
            return PurchaseObservation('apple',decoded.transactionId,account_id,decoded.productId,state,decoded.signedDate,'apple_app_store_server_api')
        except VerificationUnavailable:raise
        except Exception:raise VerificationUnavailable('Apple verification unavailable.') from None

    def acknowledge(self,observation):
        # StoreKit finishTransaction is performed by the native SDK after the
        # service grant. Apple has no Google-style server acknowledge endpoint.
        raise VerificationUnavailable('Apple completion requires the native StoreKit transaction; no server acknowledgement is asserted.')


class GooglePurchaseVerifier:
    def __init__(self, *, credentials, package_name:str, allow_test_purchases:bool,
                 purchase_token_lookup, remember_purchase_token):
        from google.auth.transport.requests import AuthorizedSession
        if not package_name or credentials is None:
            raise ValueError('Explicit Google credentials and package identity required.')
        self.http=AuthorizedSession(credentials)
        self.package_name=package_name;self.allow_test=allow_test_purchases
        # Deployment supplies protected token storage. The ledger stores only
        # a SHA-256 transaction identity, not the bearer-like purchase token.
        self.lookup=purchase_token_lookup;self.remember=remember_purchase_token

    def _url(self,token):
        return 'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/'+quote(self.package_name,safe='')+'/purchases/productsv2/tokens/'+quote(token,safe='')

    def verify(self,platform,proof,account_id):
        if platform!='google':raise VerificationUnavailable('Wrong provider.')
        value=proof_json(proof,{'purchase_token','expected_product_id'})
        try:
            response=self.http.get(self._url(value['purchase_token']),timeout=10)
            if response.status_code!=200:raise VerificationUnavailable('Google verification unavailable.')
            data=response.json();items=data.get('productLineItem',[])
            if (data.get('obfuscatedExternalAccountId')!=account_id or len(items)!=1 or
                items[0].get('productId')!=value['expected_product_id'] or
                ('testPurchaseContext' in data and not self.allow_test)):
                raise VerificationUnavailable('Google transaction binding mismatch.')
            offer=items[0].get('productOfferDetails',{})
            if offer.get('quantity',1)!=1 or offer.get('rentOfferDetails') is not None or offer.get('consumptionState')=='CONSUMPTION_STATE_CONSUMED':
                raise VerificationUnavailable('Unsupported Google purchase shape.')
            states={'PENDING':('pending',0),'PURCHASED':('purchased',1),'CANCELLED':('revoked',2)}
            state,version=states[data['purchaseStateContext']['purchaseState']]
            if state=='purchased' and offer.get('refundableQuantity') == 0:
                state,version='revoked',2
            transaction_id=hashlib.sha256(value['purchase_token'].encode()).hexdigest()
            self.remember(transaction_id,value['purchase_token'],account_id)
            return PurchaseObservation('google',transaction_id,account_id,value['expected_product_id'],state,version,'google_play_developer_api')
        except VerificationUnavailable:raise
        except Exception:raise VerificationUnavailable('Google verification unavailable.') from None

    def acknowledge(self,observation):
        if observation.platform!='google' or observation.state!='purchased':raise VerificationUnavailable('Wrong acknowledgement state.')
        token=self.lookup(observation.transaction_id,observation.account_id)
        if not token or hashlib.sha256(token.encode()).hexdigest()!=observation.transaction_id:
            raise VerificationUnavailable('Protected provider token unavailable; restore/reverify before retry.')
        # Recheck authentic current state before acknowledging. Both SDK and
        # worker may race to acknowledge; an already acknowledged response wins.
        response=self.http.get(self._url(token),timeout=10)
        if response.status_code!=200:raise VerificationUnavailable('Google acknowledgement preflight unavailable.')
        data=response.json()
        if data.get('obfuscatedExternalAccountId')!=observation.account_id or data.get('purchaseStateContext',{}).get('purchaseState')!='PURCHASED':
            raise VerificationUnavailable('Purchase is no longer eligible for acknowledgement.')
        if data.get('acknowledgementState')=='ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED':return
        url='https://androidpublisher.googleapis.com/androidpublisher/v3/applications/'+quote(self.package_name,safe='')+'/purchases/products/'+quote(observation.product_id,safe='')+'/tokens/'+quote(token,safe='')+':acknowledge'
        response=self.http.post(url,json={},timeout=10)
        if response.status_code not in {200,204}:raise VerificationUnavailable('Google acknowledgement unavailable.')


class CombinedPurchaseVerifier:
    def __init__(self, *, apple=None,google=None):self.providers={'apple':apple,'google':google}
    def verify(self,platform,proof,account_id):
        provider=self.providers.get(platform)
        if provider is None:raise VerificationUnavailable('Provider not configured.')
        return provider.verify(platform,proof,account_id)
    def acknowledge(self,observation):
        provider=self.providers.get(observation.platform)
        if provider is None:raise VerificationUnavailable('Provider not configured.')
        return provider.acknowledge(observation)
