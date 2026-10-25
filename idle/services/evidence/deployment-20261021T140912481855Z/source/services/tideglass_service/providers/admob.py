"""AdMob ECDSA server-side callback validation and account/day/slot binding."""
import base64
import json
import time
from urllib.parse import parse_qsl,unquote
import requests
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ec
from ..verification import AdObservation,VerificationUnavailable

KEY_URL='https://www.gstatic.com/admob/reward/verifier-keys.json'

class AdMobVerifier:
    def __init__(self, *, ad_unit_ids:set[str], reward_item:str='Support token', clock=time.time):
        if not ad_unit_ids or any(not value or '3940256099942544' in value for value in ad_unit_ids):
            raise ValueError('Configure real rewarded ad units explicitly.')
        self.units=frozenset(ad_unit_ids);self.reward_item=reward_item;self.clock=clock
        self._keys={};self._keys_until=0;self._last_fetch=-1e30

    def _key(self,key_id):
        if self.clock()>=self._keys_until or key_id not in self._keys:
            if self.clock()<self._last_fetch+60:raise VerificationUnavailable('Unknown ad key; refresh rate limited.')
            self._last_fetch=self.clock()
            response=requests.get(KEY_URL,timeout=10)
            if response.status_code!=200 or len(response.content)>65536:raise VerificationUnavailable('Ad verification keys unavailable.')
            data=response.json();keys={}
            for item in data['keys']:
                key=serialization.load_pem_public_key(item['pem'].encode())
                if not isinstance(key,ec.EllipticCurvePublicKey):raise VerificationUnavailable('Unexpected ad verification key.')
                keys[str(item['keyId'])]=key
            self._keys=keys;self._keys_until=self.clock()+86400
        if key_id not in self._keys:raise VerificationUnavailable('Unknown ad verification key.')
        return self._keys[key_id]

    def verify(self,proof,account_id,day_id,slot):
        try:
            # The provider signs the exact encoded query bytes before signature;
            # decoding/re-encoding this prefix would invalidate its meaning.
            prefix,suffix=proof.split('&signature=',1)
            signature_text,key_part=suffix.split('&key_id=',1)
            if '&' in key_part or not key_part.isdigit():raise ValueError()
            pairs=parse_qsl(prefix,keep_blank_values=True,strict_parsing=True)
            fields=dict(pairs)
            if len(fields)!=len(pairs):raise ValueError()
            required={'ad_network','ad_unit','custom_data','reward_amount','reward_item','timestamp','transaction_id','user_id'}
            if set(fields)!=required:raise ValueError()
            signature_text=unquote(signature_text)
            signature=base64.urlsafe_b64decode(signature_text+'='*((4-len(signature_text)%4)%4))
            self._key(key_part).verify(signature,prefix.encode(),ec.ECDSA(hashes.SHA256()))
            custom=json.loads(fields['custom_data'])
            if (custom!={'day_id':day_id,'slot':slot} or fields['user_id']!=account_id or
                fields['ad_unit'] not in self.units or fields['reward_amount']!='1' or
                fields['reward_item']!=self.reward_item or not 0<len(fields['transaction_id'])<=256 or
                abs(self.clock()*1000-int(fields['timestamp']))>3600000):raise ValueError()
            return AdObservation(fields['transaction_id'],account_id,day_id,slot,'google_admob_ecdsa_ssv')
        except VerificationUnavailable:raise
        except Exception:raise VerificationUnavailable('Ad callback signature or binding rejected.') from None


class AdMobCallbackApplication:
    """Wrap the WSGI application only after verifier and HTTPS are configured.

    No client callback token is accepted. The signed provider query is verified
    before a slot is committed through the same transactional claim function.
    """
    def __init__(self,application):self.application=application
    def __call__(self,environ,start_response):
        if environ.get('PATH_INFO')!='/providers/admob/callback':return self.application(environ,start_response)
        from ..api import ApiError
        try:
            if environ.get('REQUEST_METHOD')!='GET':raise ValueError()
            query=environ.get('QUERY_STRING','')
            if len(query)>65536:raise ValueError()
            values=dict(parse_qsl(query,keep_blank_values=True));account_id=values['user_id'];custom=json.loads(values['custom_data'])
            if set(custom)!={'day_id','slot'}:raise ValueError()
            with self.application.db.transaction() as db:
                account=db.execute('SELECT * FROM accounts WHERE id=?',(account_id,)).fetchone()
                if account is None:raise ValueError()
                # Verify even an existing slot: an unsigned callback cannot use
                # the base duplicate fast-path to impersonate a provider success.
                self.application.ad_verifier.verify(query,account_id,custom['day_id'],custom['slot'])
                self.application._support_claim(db,account,{'day_id':custom['day_id'],'slot':custom['slot'],'route':'ad','proof':query})
            status,body='200 OK',b'{"accepted":true}'
        except (ValueError,KeyError,ApiError,VerificationUnavailable):status,body='400 Bad Request',b'{"accepted":false}'
        except Exception:status,body='503 Service Unavailable',b'{"accepted":false}'
        start_response(status,[('Content-Type','application/json'),('Content-Length',str(len(body))),('Cache-Control','no-store')]);return [body]
