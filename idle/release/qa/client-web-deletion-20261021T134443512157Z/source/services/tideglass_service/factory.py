"""Explicit local configuration. No ambient credentials or generated provider success."""
from dataclasses import dataclass
import json
from pathlib import Path
from .api import Application
from .storage import Database

@dataclass
class ServiceRuntime:
    application: Application
    wsgi: object
    vault: object = None


def create_runtime(database, config_path=None, *, clock=None):
    if config_path is None:
        app=Application(database,**({'clock':clock} if clock else {}))
        return ServiceRuntime(app,app)
    # Configuration may reference service-account files. Require owner-only
    # access too; parse strictly and never print its contents on failure.
    from .vault import private_file, unique_object, VaultKeys, TokenVault
    config=json.loads(private_file(config_path),object_pairs_hook=unique_object)
    allowed={'version','google','apple','admob','ownership','soundtrack','web_deletion'}
    if not isinstance(config,dict) or set(config)-allowed or config.get('version')!=1: raise ValueError('Invalid service configuration.')
    def section(name,required,optional=()):
        value=config.get(name)
        if value is not None and (not isinstance(value,dict) or not set(required)<=value.keys() or value.keys()-set(required)-set(optional)):
            raise ValueError('Invalid configured service section.')
        return value
    def path(value):
        candidate=Path(value)
        if not candidate.is_absolute(): raise ValueError('Configuration file paths must be absolute.')
        return candidate
    db=Database(database)
    google=apple=ad=signer=soundtrack=vault=identity=None
    g=section('google',{'credentials_file','package_name','allow_test_purchases','vault_key_file'}, {'push_audience','push_service_account'})
    if g:
        if type(g['allow_test_purchases']) is not bool: raise ValueError('Explicit test-purchase policy required.')
        from google.oauth2 import service_account
        from .providers.stores import GooglePurchaseVerifier
        from .providers.notifications import GooglePushIdentity
        credentials=service_account.Credentials.from_service_account_info(json.loads(private_file(path(g['credentials_file']))),scopes=['https://www.googleapis.com/auth/androidpublisher'])
        vault=TokenVault(db,VaultKeys(path(g['vault_key_file'])))
        google=GooglePurchaseVerifier(credentials=credentials,package_name=g['package_name'],allow_test_purchases=g['allow_test_purchases'],purchase_token_lookup=vault.lookup,remember_purchase_token=vault.remember)
        if 'push_audience' in g or 'push_service_account' in g:
            identity=GooglePushIdentity(g['push_audience'],g['push_service_account'])
    a=section('apple',{'signing_key_file','key_id','issuer_id','bundle_id','root_certificate_files','environment'},{'app_apple_id'})
    if a:
        from .providers.stores import ApplePurchaseVerifier
        if not isinstance(a['root_certificate_files'],list) or not 1<=len(a['root_certificate_files'])<=8: raise ValueError('Apple trusted roots required.')
        roots=[path(p).read_bytes() for p in a['root_certificate_files']]
        if any(not 0<len(p)<=65536 for p in roots): raise ValueError('Invalid Apple trusted root.')
        apple=ApplePurchaseVerifier(signing_key=private_file(path(a['signing_key_file'])),key_id=a['key_id'],issuer_id=a['issuer_id'],bundle_id=a['bundle_id'],root_certificates=roots,environment=a['environment'],app_apple_id=a.get('app_apple_id'))
    o=section('ownership',{'private_key_file','issuer'},{'ttl_seconds','allow_local_development'})
    if o:
        from .leases import OwnershipSigner
        signer=OwnershipSigner(path(o['private_key_file']),o['issuer'],ttl=o.get('ttl_seconds',86400),allow_local_development=o.get('allow_local_development',False))
    s=section('soundtrack',{'archive_file','sha256'})
    if s:
        from .soundtrack import SoundtrackAsset
        soundtrack=SoundtrackAsset(path(s['archive_file']),s['sha256'])
    ads=section('admob',{'callback_ad_unit_ids'})
    if ads:
        from .providers.admob import AdMobVerifier
        if not isinstance(ads['callback_ad_unit_ids'],list): raise ValueError('Ad unit allowlist required.')
        ad=AdMobVerifier(ad_unit_ids=set(ads['callback_ad_unit_ids']),**({'clock':clock} if clock else {}))
    verifier=None
    if google or apple:
        from .providers.stores import CombinedPurchaseVerifier
        verifier=CombinedPurchaseVerifier(google=google,apple=apple)
    app=Application(db,purchase_verifier=verifier,ad_verifier=ad,token_vault=vault,ownership_signer=signer,soundtrack=soundtrack,**({'clock':clock} if clock else {}))
    wrapped=app
    if ad:
        from .providers.admob import AdMobCallbackApplication
        wrapped=AdMobCallbackApplication(app)
    if google or apple:
        from .providers.notifications import StoreNotificationApplication
        wrapped=StoreNotificationApplication(app,downstream=wrapped,apple=apple,google=google,google_identity=identity)
    web=section('web_deletion',{'origin'},{'allow_loopback_http'})
    if web:
        from .web_deletion import DeletionWebApplication
        wrapped=DeletionWebApplication(wrapped,origin=web['origin'],
                                       allow_loopback_http=web.get('allow_loopback_http',False))
    return ServiceRuntime(app,wrapped,vault)
