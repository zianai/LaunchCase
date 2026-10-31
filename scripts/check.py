"""Run a reproducible command, retaining actual output and exit status."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

phase, *command = sys.argv[1:]
root = Path(__file__).resolve().parents[1]
folder = root / 'docs/evidence' / phase
folder.mkdir(parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(folder / f'{stamp}.log').write_text(result.stdout)
(folder / f'{stamp}.json').write_text(json.dumps({'command': command, 'exit_code': result.returncode, 'log': f'docs/evidence/{phase}/{stamp}.log'}, indent=2))
print(result.stdout)
print(f'EXIT_CODE={result.returncode}')
sys.exit(result.returncode)
