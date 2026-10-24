"""Presentation-only packet v2: preserve v1 and remove study labels from rubric."""
import json
from pathlib import Path
from supplements.exploration_003.common import HERE,ROOT,REPORTS,CACHE,read,write,sha256
from supplements.exploration_003.packet import blank_ratings
from supplements.exploration_003.analysis import verify_science


def reviewer_codebook(text: str) -> str:
    semantic = text.split('## Layer2: human semantic strategies\n', 1)[1]
    return ('# Trajectory review rubric\n\n'
        'Rate the supplied windows independently. False claims can be coherent, '
        'task-relevant strategies; factual correctness is a separate question. '
        'Judge actual text and visible evidence, not action API labels. '
        'Offline truth is reviewer material and was not supplied to the actors. '
        'Missing context should produce uncertainty, not an invented intention.\n\n'
        + semantic)


def preserve_or_write(path: Path, text: str) -> None:
    if path.exists() and path.read_text() != text:
        raise ValueError('Refusing to replace existing review content: '+str(path))
    if not path.exists():path.write_text(text)


def main() -> None:
    verify_science()
    old=CACHE/'human_review/reviewer';new=CACHE/'human_review/reviewer_v2'
    manifest=read(REPORTS/'HUMAN_REVIEW_MANIFEST.json')
    for name,digest in manifest['reviewer_files'].items():
        # Rating forms are allowed to acquire human annotations, but never replaced.
        if not name.startswith('rater_') and sha256(old/name)!=digest:
            raise ValueError('Original packet content changed')
    new.mkdir(exist_ok=True)
    for name in ('items.json','PACKET.md'):
        preserve_or_write(new/name,(old/name).read_text())
    preserve_or_write(new/'CODEBOOK.md',reviewer_codebook((HERE/'CODEBOOK.md').read_text()))
    items=read(old/'items.json')
    # A new version must not discard annotations already present in v1.
    import csv
    for number in (1,2):
        with (old/f'rater_{number}.csv').open() as source:
            annotated=any(any(v.strip() for k,v in row.items() if k!='item_id') for row in csv.DictReader(source))
        if annotated:raise ValueError('v1 has annotations: migrate explicitly before preparing v2')
        blank_ratings(new/f'rater_{number}.csv',items)
    write(REPORTS/'HUMAN_REVIEW_V2_MANIFEST.json',{
        'version':2,'items':len(items),'changes':'Only the reviewer rubric presentation changes; v1 retained. Layer-1 study-specific ablation labels are omitted. Item bytes, order and IDs unchanged.',
        'reviewer_directory':str(new.relative_to(ROOT)),
        'private_directory':manifest['private_directory'],
        'source_v1_manifest_sha256':sha256(REPORTS/'HUMAN_REVIEW_MANIFEST.json'),
        'scientific_codebook_sha256':sha256(HERE/'CODEBOOK.md'),
        'presentation_script_sha256':sha256(Path(__file__)),
        'files':{p.name:sha256(p) for p in sorted(new.iterdir()) if p.is_file()},
        'items_identical_to_v1':sha256(new/'items.json')==sha256(old/'items.json'),
        'private_mapping_sha256':manifest['private_mapping_sha256'],
        'status':'Human labels pending; metadata blinding cannot hide cast size or behavioral differences.'})
    print({'reviewer_directory':str(new.relative_to(ROOT)),'items':len(items),'version':2})


if __name__=='__main__':main()
