import requests
from pathlib import Path

base = 'http://127.0.0.1:8001'
user = {
    'display_name': 'Version Compare E2E User',
    'username': 'versioncomparee2e',
    'email': 'versioncomparee2e@example.com',
    'password': 'Test@1234'
}
requests.post(f'{base}/api/auth/register', json=user, timeout=20)
login = requests.post(f'{base}/api/auth/login', json={'username': user['username'], 'password': user['password']}, timeout=20)
login.raise_for_status()
token = login.json()['access_token']
path = Path(r'c:\Users\thaizy.castro\Downloads\ext_verBEATRIZ.log')
with path.open('rb') as handle:
    response = requests.post(
        f'{base}/api/version-compare',
        files={'log_file': (path.name, handle, 'text/plain')},
        headers={'Authorization': f'Bearer {token}'},
        timeout=300,
    )
print('STATUS=' + str(response.status_code))
body = response.json()
if response.ok:
    print('PRODUCT_VERSION=' + str(body.get('product_version')))
    summary = body.get('summary') or {}
    print('TOTAL_PROGRAMAS_CLIENTE=' + str(summary.get('total_programas_cliente')))
    print('TOTAL_COMPARADOS=' + str(summary.get('total_comparados')))
    print('DESATUALIZADOS=' + str(summary.get('desatualizados')))
    print('OK=' + str(summary.get('ok')))
    print('ADIANTADO=' + str(summary.get('adiantado_customizado')))
    print('NAO_ENCONTRADO=' + str(summary.get('nao_encontrado')))
    first_outdated = (body.get('desatualizados') or [])[:3]
    print('OUTDATED_SAMPLE=' + str(first_outdated))
else:
    print('DETAIL=' + str(body.get('detail')))
