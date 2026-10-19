"""Generate local-only secrets. Never print them or commit .env."""
from pathlib import Path
import secrets
root = Path(__file__).resolve().parents[1]
env = root / '.env'
if not env.exists():
    env.write_text('\n'.join(f'{name}={secrets.token_hex(24)}' for name in
                   ('DB_PASSWORD', 'CONTROL_TOKEN', 'GRAFANA_PASSWORD')) + '\n')
print('Sandbox environment ready; secrets remain in ignored .env')
