"""Set up the repo on a fresh machine that has conda.

Creates a local conda env (default ./env at the repo root) with Python 3.12.12,
installs requirements.txt, then runs scripts/verify_installation.py.

Run with any Python (e.g. conda's base env):
    python scripts/setup.py
    python scripts/setup.py --recreate          # delete and rebuild the env
    python scripts/setup.py --env-path ./myenv --skip-verify

Afterwards:
    conda activate ./env
    cd src
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON_VERSION = '3.12.12'
PROMPTING_PACKAGES = ['requests', 'python-dotenv']


def run(cmd: list[str], **kwargs):
    print('$ ' + ' '.join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kwargs)


def find_conda() -> str:
    for cand in [os.environ.get('CONDA_EXE'), shutil.which('conda'), shutil.which('mamba')]:
        if cand and Path(cand).exists():
            return cand
    sys.exit('conda not found. Install Miniconda/Miniforge or make sure `conda` is on PATH.')


def env_python(env: Path) -> Path:
    return env / ('python.exe' if os.name == 'nt' else 'bin/python')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--env-path', default=str(ROOT / 'env'), help='where to create the conda env (default: <repo>/env)')
    parser.add_argument('--recreate', action='store_true', help='delete the env first if it already exists')
    parser.add_argument('--no-prompting', action='store_true', help=f'skip {", ".join(PROMPTING_PACKAGES)} (only needed to prompt new automata)')
    parser.add_argument('--skip-verify', action='store_true', help='do not run scripts/verify_installation.py at the end')
    args = parser.parse_args()

    env = Path(args.env_path).expanduser().resolve()
    conda = find_conda()

    if env.exists() and args.recreate:
        print(f'Removing existing env {env}')
        run([conda, 'env', 'remove', '-y', '-p', env])
        shutil.rmtree(env, ignore_errors=True)

    py = env_python(env)
    if py.exists():
        print(f'Reusing existing env {env} (pass --recreate to rebuild it)')
    else:
        run([conda, 'create', '-y', '-p', env, f'python={PYTHON_VERSION}'])

    run([py, '-m', 'ensurepip', '--upgrade'])
    run([py, '-m', 'pip', 'install', '--upgrade', 'pip'])
    run([py, '-m', 'pip', 'install', '-r', ROOT / 'requirements.txt'])
    if not args.no_prompting:
        run([py, '-m', 'pip', 'install', *PROMPTING_PACKAGES])

    for d in ['logs', 'temp']:
        (ROOT / d).mkdir(exist_ok=True)

    if not (ROOT / '.env').exists() and not args.no_prompting:
        print('\nNote: prompting new automata needs an OpenRouter key in a .env file at the repo root.')

    if not args.skip_verify:
        print()
        run([py, ROOT / 'scripts' / 'verify_installation.py'])

    rel = os.path.relpath(env, Path.cwd())
    print(f'\nSetup done. Activate with:\n    conda activate {rel if not rel.startswith("..") else env}\n    cd {ROOT / "src"}')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f'\nSetup failed: command exited with code {e.returncode}')
