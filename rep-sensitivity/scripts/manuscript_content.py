"""Atomic updates to the one-file paper. This module never runs inference.

Authored prose lives in main.tex. Only explicitly delimited result blocks may be
replaced. Figures are ordinary local files, not external TeX dependencies.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'manuscript/main.tex'


def replace_block(text, name, content):
    start, end = '% BEGIN AUTO: ' + name, '% END AUTO: ' + name
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError('Expected one manuscript block: ' + name)
    before, tail = text.split(start, 1)
    _, after = tail.split(end, 1)
    return before + start + '\n' + content.rstrip() + '\n' + end + after


def validate_single_source(text, directory):
    if re.search(r'\\(?:input|include|bibliography|bibliographystyle)\s*\{', text):
        raise ValueError('The manuscript must compile from one TeX source')
    for name in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', text):
        if Path(name).name != name or not (directory / name).is_file():
            raise ValueError('Figure must exist beside main.tex: ' + name)
    if any(ord(c) > 127 for c in text):
        raise ValueError('Use ASCII manuscript source')
    if r'\begin{thebibliography}' not in text:
        raise ValueError('An inline bibliography is required')


@contextmanager
def manuscript_lock():
    folder = ROOT / 'artifacts'
    folder.mkdir(exist_ok=True)
    with (folder / 'manuscript-update.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def update_blocks(blocks):
    with manuscript_lock():
        previous = PAPER.read_text()
        updated = previous
        for name, content in blocks.items():
            updated = replace_block(updated, name, content)
        validate_single_source(updated, PAPER.parent)
        if updated != previous:
            temporary = PAPER.with_suffix('.tex.tmp')
            temporary.write_text(updated)
            temporary.replace(PAPER)
    return updated != previous


def completed(suite):
    path = ROOT / 'results' / suite / 'analysis.json'
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return data if data.get('complete') else None


def copy_figure(source, basename):
    if Path(basename).name != basename:
        raise ValueError(basename)
    destination = PAPER.parent / basename
    if not destination.exists() or source.read_bytes() != destination.read_bytes():
        shutil.copyfile(source, destination)
    return basename


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference_record(text=None):
    text = PAPER.read_text() if text is None else text
    version = re.search(r'^% MANUSCRIPT_VERSION: (\d+)\s*$', text, re.M)
    number = version.group(1) if version else '6'
    return ROOT / f'records/reference-verification-v{number}.json'


def refresh():
    # Imported lazily so that report builders can keep their existing CPU-only
    # entry points without circular imports or changes to frozen experiment code.
    from build_manuscript import build
    return build()


def compile_if_changed():
    """Keep the PDF current after each completed stage, without needless builds.

    The marker is written only after compilation and structural checks succeed.
    Partial-stage reporting never changes the full-study completion gate.
    """
    assets = [PAPER, *sorted(p for p in PAPER.parent.glob('*.pdf') if p.name != 'main.pdf'),
              ROOT / 'scripts/check_manuscript.py', reference_record()]
    signature = hashlib.sha256(''.join(sha(p) for p in assets).encode()).hexdigest()
    marker = ROOT / 'artifacts/manuscript-compiled.json'
    if marker.exists() and (PAPER.parent / 'main.pdf').exists():
        old = json.loads(marker.read_text())
        if old.get('source_sha256') == signature and old.get('pdf_sha256') == sha(PAPER.parent / 'main.pdf'):
            return False
    subprocess.run(['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error', 'main.tex'],
                   cwd=PAPER.parent, check=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/check_manuscript.py')], cwd=ROOT, check=True)
    marker.write_text(json.dumps({'source_sha256': signature,
                                 'pdf_sha256': sha(PAPER.parent / 'main.pdf')}, indent=2) + '\n')
    return True
