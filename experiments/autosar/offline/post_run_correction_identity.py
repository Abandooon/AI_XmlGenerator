"""Portable reviewer identity/path checks, added 2026-09-09.

This replaces the missing legacy import for the supported offline entrypoint.
It does not rewrite or re-sign the frozen experiment and does not execute repairs.
"""
from pathlib import Path, PurePosixPath
import hashlib
import json
import zipfile


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def canonical_valid(value):
    return canonical_sha256({k:v for k,v in value.items() if k != 'content_sha256'}) == value.get('content_sha256')


def under(root, relative):
    """Accept archive-relative paths only, on both Windows and POSIX."""
    relative = str(relative).replace('\\', '/')
    parts = PurePosixPath(relative).parts
    if not parts or relative.startswith('/') or ':' in relative or '..' in parts:
        raise ValueError('Unsafe relative archive path: '+relative)
    root = Path(root).resolve()
    target = root.joinpath(*parts).resolve()
    if not target.is_relative_to(root):
        raise ValueError('Path leaves requested root')
    return target


def relocate_evidence(release, recorded_path, track):
    marker = '/'+track+'/'
    value = str(recorded_path).replace('\\', '/')
    if marker not in value:
        raise ValueError('Recorded path lacks expected evidence track: '+track)
    return under(Path(release)/'evidence/formal_v20'/track, value.split(marker, 1)[1])


def verify_file_map(root, files):
    failures = []
    for relative, expected in files.items():
        target = under(root, relative)
        if not target.is_file() or sha256_file(target) != expected:
            failures.append(relative)
    return {'checked':len(files), 'errors':failures}


def extract_archive(archive, destination, expected_sha256):
    """Never overwrite a previous workspace; the caller owns the fresh directory."""
    if sha256_file(archive) != expected_sha256:
        raise ValueError('Original frozen ZIP hash mismatch')
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        names = set()
        for item in z.infolist():
            target = under(destination, item.filename)
            key = str(target).casefold()
            if key in names:
                raise ValueError('Duplicate ZIP entry')
            names.add(key)
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Symlink in frozen archive')
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(item) as source, target.open('xb') as out:
                    import shutil
                    shutil.copyfileobj(source, out)
    manifests = list(destination.glob('*/RELEASE_MANIFEST.json'))
    if len(manifests) != 1:
        raise ValueError('Expected exactly one release root')
    return manifests[0].parent
