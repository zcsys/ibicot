"""Independent provider policy probes. Uses provider response doubles, never store credentials."""
import base64,copy,importlib.util,json,sys,unittest
from pathlib import Path
from urllib.parse import urlencode
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
ROOT=Path(sys.argv[1]);sys.path.insert(0,str(ROOT));sys.argv=sys.argv[:1]
spec=importlib.util.spec_from_file_location('provider_fixture',ROOT/'tests/services/providers/test_provider_adapters.py'); fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
from services.tideglass_service.providers.admob import AdMobVerifier
from services.tideglass_service.verification import VerificationUnavailable
class IndependentProviderReview(unittest.TestCase):
 def test_google_rejects_ungrantable_shapes_and_maps_full_refund(self):
  helper=fixture.ProviderTests()
  for patch in [{'quantity':2},{'rentOfferDetails':{}},{'consumptionState':'CONSUMPTION_STATE_CONSUMED'}]:
   with self.subTest(patch=patch):
    verifier,data=helper.google();data['productLineItem'][0]['productOfferDetails'].update(patch)
    with self.assertRaises(VerificationUnavailable):verifier.verify('google',helper.proof(),fixture.ACCOUNT)
  verifier,data=helper.google();data['productLineItem'][0]['productOfferDetails']['refundableQuantity']=0
  self.assertEqual(verifier.verify('google',helper.proof(),fixture.ACCOUNT).state,'revoked')
 def test_google_proof_schema_cannot_trigger_provider_lookup(self):
  helper=fixture.ProviderTests()
  for raw in ['{}','[]','null',json.dumps({'purchase_token':'opaque','expected_product_id':fixture.PRODUCT,'account_id':fixture.ACCOUNT}),json.dumps({'purchase_token':'opaque','expected_product_id':'forged'})]:
   with self.subTest(proof=raw):
    verifier,_=helper.google()
    with self.assertRaises(VerificationUnavailable):verifier.verify('google',raw,fixture.ACCOUNT)
    verifier.http.get.assert_not_called()
 def test_valid_crypto_is_insufficient_without_exact_reward_binding(self):
  private=ec.generate_private_key(ec.SECP256R1()); verifier=AdMobVerifier(ad_unit_ids={'approved'},clock=lambda:100000);verifier._keys={'1':private.public_key()};verifier._keys_until=200000
  fields={'ad_network':'test','ad_unit':'approved','custom_data':json.dumps({'day_id':1,'slot':0}),'reward_amount':'1','reward_item':'Support token','timestamp':'100000000','transaction_id':'test-only-ad','user_id':fixture.ACCOUNT}
  for patch in [{'ad_unit':'unapproved'},{'reward_amount':'2'},{'reward_item':'currency'},{'custom_data':json.dumps({'day_id':1,'slot':1})},{'user_id':'other'},{'timestamp':'96399000'},{'timestamp':'103601000'}]:
   with self.subTest(patch=patch):
    prefix=urlencode({**fields,**patch});sig=private.sign(prefix.encode(),ec.ECDSA(hashes.SHA256()));query=prefix+'&signature='+base64.urlsafe_b64encode(sig).decode().rstrip('=')+'&key_id=1'
    with self.assertRaises(VerificationUnavailable):verifier.verify(query,fixture.ACCOUNT,1,0)
 def test_duplicate_signed_parameters_and_unsigned_suffix_rejected(self):
  private=ec.generate_private_key(ec.SECP256R1());verifier=AdMobVerifier(ad_unit_ids={'approved'},clock=lambda:100000);verifier._keys={'1':private.public_key()};verifier._keys_until=200000
  prefix=urlencode({'ad_network':'test','ad_unit':'approved','custom_data':json.dumps({'day_id':1,'slot':0}),'reward_amount':'1','reward_item':'Support token','timestamp':'100000000','transaction_id':'test-only','user_id':fixture.ACCOUNT})
  for extra,suffix in [('&reward_amount=1',''),('','&reward_amount=1')]:
   signed=prefix+extra;sig=private.sign(signed.encode(),ec.ECDSA(hashes.SHA256()));query=signed+'&signature='+base64.urlsafe_b64encode(sig).decode().rstrip('=')+'&key_id=1'+suffix
   with self.assertRaises(VerificationUnavailable):verifier.verify(query,fixture.ACCOUNT,1,0)
if __name__=='__main__':unittest.main(verbosity=2)
