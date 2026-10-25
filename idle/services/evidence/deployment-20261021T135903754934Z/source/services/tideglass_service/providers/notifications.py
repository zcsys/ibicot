"""Authenticated notifications trigger a fresh provider read, never direct grants."""
import base64
import hashlib
import json
from ..verification import VerificationUnavailable
from ..reconcile import purchase_proof

class GooglePushIdentity:
    def __init__(self, audience, service_account_email):
        if not audience.startswith('https://') or not service_account_email.endswith('.gserviceaccount.com'):
            raise ValueError('Explicit HTTPS audience and push service-account email required.')
        self.audience, self.email = audience, service_account_email
    def verify(self, header):
        from google.oauth2 import id_token
        from google.auth.transport.requests import Request
        if not isinstance(header,str) or not header.startswith('Bearer ') or len(header)>16384:
            raise VerificationUnavailable('Push authentication required.')
        class BoundedRequest(Request):
            def __call__(self,*args,**kwargs):
                kwargs['timeout']=10
                return super().__call__(*args,**kwargs)
        try:
            claims=id_token.verify_oauth2_token(header[7:],BoundedRequest(),self.audience)
            if claims.get('email')!=self.email or claims.get('email_verified') is not True or claims.get('iss') not in {'accounts.google.com','https://accounts.google.com'}:
                raise ValueError()
        except Exception: raise VerificationUnavailable('Push identity rejected.') from None

class StoreNotificationApplication:
    def __init__(self, application, *, downstream=None, apple=None, google=None, google_identity=None):
        self.application=application;self.downstream=downstream or application
        self.apple,self.google,self.google_identity=apple,google,google_identity
    def __call__(self,environ,start_response):
        path=environ.get('PATH_INFO')
        if path not in {'/providers/apple/notifications','/providers/google/notifications'}:
            return self.downstream(environ,start_response)
        from ..api import strict_json, ApiError
        try:
            if environ.get('REQUEST_METHOD')!='POST' or environ.get('QUERY_STRING') or environ.get('HTTP_TRANSFER_ENCODING'):
                raise ValueError()
            length=int(environ.get('CONTENT_LENGTH','0'))
            if not 0<length<=262144 or environ.get('CONTENT_TYPE','').split(';')[0]!='application/json': raise ValueError()
            self.application._rate_limit(environ.get('REMOTE_ADDR','unknown'),path)
            raw=environ['wsgi.input'].read(length)
            if len(raw)!=length: raise ValueError()
            body=strict_json(raw)
            if path.endswith('/apple/notifications'):
                if self.apple is None: raise VerificationUnavailable()
                if not isinstance(body,dict) or set(body)!={'signedPayload'} or not isinstance(body['signedPayload'],str): raise ValueError()
                notification=self.apple.verifier.verify_and_decode_notification(body['signedPayload'])
                if notification.data is None or not notification.data.signedTransactionInfo:
                    # Signed TEST notifications need no ownership mutation.
                    if notification.rawNotificationType!='TEST': raise ValueError()
                    row=None
                else:
                    decoded=self.apple.verifier.verify_and_decode_signed_transaction(notification.data.signedTransactionInfo)
                    with self.application.db.read() as db:
                        row=db.execute("SELECT * FROM purchases WHERE platform='apple' AND transaction_id=?",(decoded.transactionId,)).fetchone()
                    if row and (str(decoded.appAccountToken).lower()!=row['account_id'].lower() or decoded.productId!=row['product_id']): raise ValueError()
            else:
                if self.google is None or self.google_identity is None: raise VerificationUnavailable()
                self.google_identity.verify(environ.get('HTTP_AUTHORIZATION'))
                message=body['message']
                data=strict_json(base64.b64decode(message['data'],validate=True))
                if data['packageName']!=self.google.package_name: raise ValueError()
                event=data.get('oneTimeProductNotification') or data.get('voidedPurchaseNotification')
                if event is None:
                    if 'testNotification' not in data: raise ValueError()
                    row=None
                else:
                    token=event['purchaseToken']
                    if not isinstance(token,str) or not 0<len(token)<=65536: raise ValueError()
                    transaction=hashlib.sha256(token.encode()).hexdigest()
                    with self.application.db.read() as db:
                        row=db.execute("SELECT * FROM purchases WHERE platform='google' AND transaction_id=?",(transaction,)).fetchone()
            if row:
                proof=purchase_proof(row,self.application.token_vault)
                with self.application.db.transaction() as db:
                    self.application._enabled(db,'purchases')
                    if db.execute('SELECT 1 FROM accounts WHERE id=?',(row['account_id'],)).fetchone():
                        self.application._purchase(db,row['account_id'],{'platform':row['platform'],'proof':json.dumps(proof)})
            # Unknown/deleted transactions are never resurrected by notifications.
            status,result='200 OK',{'accepted':True}
        except VerificationUnavailable: status,result='503 Service Unavailable',{'accepted':False}
        except (ValueError,TypeError,KeyError,AttributeError,ApiError): status,result='400 Bad Request',{'accepted':False}
        except Exception: status,result='503 Service Unavailable',{'accepted':False}
        encoded=json.dumps(result,separators=(',',':')).encode()
        start_response(status,[('Content-Type','application/json'),('Content-Length',str(len(encoded))),('Cache-Control','no-store')])
        return [encoded]
