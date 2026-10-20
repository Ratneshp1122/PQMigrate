"""Build fixed API/name rules, not rules learned from evaluation labels.

JSON is a YAML subset accepted by Semgrep; generated .yaml files are committed.
Only engineering fixtures may motivate matcher repairs. Do not consume labels.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rules = {'python': [], 'go': []}
policies = {}


def add(lang, name, patterns, op='uncertain', role='uncertain', certain=False):
    rid = f'pqmigrate.{lang}.{name}'
    policy = {'presence': 'yes' if certain else 'uncertain', 'operation': op if certain else 'uncertain',
              'role': role if certain else 'uncertain',
              'evidence_kind': 'qualified_api_syntax' if certain else 'unresolved_call_syntax',
              'uncertainty_reason': '' if certain else 'Receiver/provider identity is not established by this syntax-only rule. Method name is not cryptographic proof.',
              'candidate_operation': op}
    rules[lang].append({'id': rid, 'languages': [lang], 'severity': 'INFO',
                        'message': f'Crypto API/candidate call ({op}); source review required.',
                        'metadata': {'baseline': 'pqmigrate-semgrep-v1', **policy}, **patterns})
    policies[rid] = {k:v for k,v in policy.items() if k != 'candidate_operation'}


def either(patterns):
    return {'pattern-either': [{'pattern': p} for p in patterns]}


add('python', 'hashlib', {'patterns': [{'pattern': 'hashlib.$H(...)'},
    {'metavariable-regex': {'metavariable': '$H', 'regex': '^(md5|sha1|sha224|sha256|sha384|sha512|sha3_224|sha3_256|sha3_384|sha3_512|blake2b|blake2s|shake_128|shake_256|new)$'}}]}, 'hash', 'hash', True)
add('python', 'hmac', either(['hmac.new(...)', 'hmac.digest(...)',
    'cryptography.hazmat.primitives.hmac.HMAC(...)']), 'mac', 'mac', True)
add('python', 'key-generation', either([
    'cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key(...)',
    'cryptography.hazmat.primitives.asymmetric.ec.generate_private_key(...)',
    'cryptography.hazmat.primitives.asymmetric.dsa.generate_private_key(...)',
    *[f'cryptography.hazmat.primitives.asymmetric.{module}.{cls}.generate(...)' for module,cls in [
        ('ed25519','Ed25519PrivateKey'),('ed448','Ed448PrivateKey'),
        ('x25519','X25519PrivateKey'),('x448','X448PrivateKey'),
        ('mlkem','MLKEM768PrivateKey'),('mlkem','MLKEM1024PrivateKey')]]
]), 'key_generate', 'key_management', True)
add('python', 'key-loading', either([f'cryptography.hazmat.primitives.serialization.{method}(...)' for method in [
    'load_pem_private_key','load_der_private_key','load_pem_public_key','load_der_public_key','load_ssh_private_key','load_ssh_public_key']]), 'other_crypto','key_management',True)
add('python', 'hash-context', {'pattern': 'cryptography.hazmat.primitives.hashes.Hash(...)'}, 'hash','hash',True)
for method, op in [('sign','sign'),('verify','verify'),('encrypt','encrypt'),('decrypt','decrypt'),
                   ('exchange','key_establish'),('encapsulate','key_establish'),('decapsulate','key_establish'),
                   ('digest','hash'),('hexdigest','hash'),('finalize','uncertain'),('derive','kdf')]:
    add('python', f'candidate-{method}', {'pattern': f'$RECEIVER.{method}(...)'}, op)

# Bind a package identifier through an explicit import, including aliased imports.
# These remain candidates: syntax alone cannot establish unshadowed package identity.
for package, methods, op in [
    ('crypto/rsa',['GenerateKey','GenerateMultiPrimeKey'],'key_generate'),
    ('crypto/ecdsa',['GenerateKey'],'key_generate'),('crypto/ed25519',['GenerateKey'],'key_generate'),
    ('crypto/rsa',['SignPKCS1v15','SignPSS'],'sign'),
    ('crypto/rsa',['VerifyPKCS1v15','VerifyPSS'],'verify'),
    ('crypto/rsa',['EncryptPKCS1v15','EncryptOAEP'],'encrypt'),
    ('crypto/rsa',['DecryptPKCS1v15','DecryptPKCS1v15SessionKey','DecryptOAEP'],'decrypt'),
    ('crypto/aes',['NewCipher'],'other_crypto'),('crypto/cipher',['NewGCM','NewGCMWithNonceSize','NewGCMWithTagSize'],'other_crypto'),
    ('crypto/hmac',['New'],'mac'),('crypto/sha256',['Sum256','Sum224'],'hash'),
    ('crypto/sha512',['Sum512','Sum384','Sum512_224','Sum512_256'],'hash'),
    ('crypto/sha1',['Sum'],'hash'),('crypto/md5',['Sum'],'hash'),
]:
    default = package.rsplit('/',1)[-1]
    binding = {'pattern-either': [
        {'patterns':[{'pattern-inside': f'package $P\nimport "{package}"\n...'},
                     either([f'{default}.{m}(...)' for m in methods])]},
        {'patterns':[{'pattern-inside': f'package $P\nimport $PKG "{package}"\n...'},
                     either([f'$PKG.{m}(...)' for m in methods])]},
    ]}
    add('go', package.replace('/','-')+'-'+op, binding, op)
for method,op in [('Sign','sign'),('Verify','verify'),('Encrypt','encrypt'),('Decrypt','decrypt'),
                  ('GenerateKey','key_generate'),('ECDH','key_establish'),('Encapsulate','key_establish'),
                  ('Decapsulate','key_establish'),('Sum','hash'),('Seal','encrypt'),('Open','decrypt')]:
    add('go',f'candidate-{method.lower()}',{'pattern':f'$RECEIVER.{method}(...)'},op)

for lang, entries in rules.items():
    dest = HERE/'rules'/f'{lang}.yaml'
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps({'rules':entries},indent=2)+'\n',encoding='utf-8')
(HERE/'mapping.json').write_text(json.dumps(policies,indent=2,sort_keys=True)+'\n',encoding='utf-8')
