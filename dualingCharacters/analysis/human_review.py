"""Offline blinded packet and descriptive inter-rater agreement; no model calls.

This reporting extension does not manufacture ratings or adjudicate disagreements.
The private condition key supplies scenario clusters only to the analysis, never
to the reviewer-facing HTML. Missing ratings stay missing.
"""
from pathlib import Path
import csv
import hashlib
import html
import json
import numpy as np

ITEMS = ("site", "mode", "cap", "day", "audience", "partner", "transport",
         "equipment", "update_authority", "clarification")
CATEGORIES = ("0", "1", "NA")


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_ratings(path: Path, expected_ids: set[str]) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["id", *ITEMS, "comments"]:
            raise ValueError(f"Unexpected rating columns: {path.name}")
        ratings = {}
        for row in reader:
            identity = row["id"]
            if identity not in expected_ids or identity in ratings:
                raise ValueError("Unknown or duplicate blinded output ID")
            if None in row or any(value is None for value in row.values()):
                raise ValueError("Malformed CSV row")
            for item in ITEMS:
                if row[item] not in ("", *CATEGORIES):
                    raise ValueError(f"Invalid rating for {identity}/{item}")
            ratings[identity] = row
    return ratings


def agreement(pairs: list[tuple[str, str]]) -> dict:
    if not pairs:
        return {"paired_ratings": 0, "raw_agreement": None, "cohen_kappa": None}
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    expected = sum(sum(a == value for a, _ in pairs) *
                   sum(b == value for _, b in pairs) for value in CATEGORIES) / n**2
    return {"paired_ratings": n, "raw_agreement": observed,
            "cohen_kappa": (observed - expected) / (1 - expected) if expected < 1 else None}


def cluster_intervals(records: list[dict], draws: int = 10000) -> dict:
    """Resample whole scenario families, retaining worlds, conditions and items."""
    families = sorted({row["family"] for row in records})
    if len(families) < 2:
        return {"family_clusters": len(families), "raw_agreement_ci95": None,
                "cohen_kappa_ci95": None, "valid_kappa_draws": 0}
    counts = np.zeros((len(families), 3, 3), dtype=np.int64)
    family_index = {value: i for i, value in enumerate(families)}
    for row in records:
        counts[family_index[row["family"]], CATEGORIES.index(row["a"]), CATEGORIES.index(row["b"])] += 1
    rng = np.random.default_rng(40720)
    matrices = counts[rng.integers(0, len(families), size=(draws, len(families)))].sum(axis=1)
    totals = matrices.sum(axis=(1, 2))
    observed = np.trace(matrices, axis1=1, axis2=2) / totals
    expected = (matrices.sum(axis=1) * matrices.sum(axis=2)).sum(axis=1) / totals**2
    defined = expected < 1
    kappas = (observed[defined] - expected[defined]) / (1 - expected[defined])
    return {"family_clusters": len(families), "bootstrap_draws": draws,
            "raw_agreement_ci95": np.quantile(observed, [.025, .975]).tolist(),
            "cohen_kappa_ci95": np.quantile(kappas, [.025, .975]).tolist() if len(kappas) else None,
            "valid_kappa_draws": int(defined.sum())}


def render_packet(packet: list[dict], destination: Path) -> None:
    """Readable local artifact; no private key, network assets, scripts or labels."""
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<title>Blinded planning-response review</title>',
             '<style>body{max-width:72em;margin:2em auto;font:17px/1.5 sans-serif;padding:0 1em}'
             'pre{white-space:pre-wrap;overflow-wrap:anywhere}article{border-top:2px solid #666;margin-top:3em}'
             'table{border-collapse:collapse}td,th{border:1px solid #888;padding:.3em .7em}</style>',
             '<h1>Blinded planning-response review</h1><p>Score the final prose answer using the fixed rubric '
             'and your independent CSV sheet. The generated working context may contain errors. '
             'Use attributed original user sources and the reference state for authority. '
             'Do not exchange ratings before both independent sheets are locked.</p>']
    for row in packet:
        parts.append('<article><h2>' + html.escape(row['id']) + '</h2><h3>Final response</h3><pre>' +
                     html.escape(row['response']) + '</pre><h3>Reference state for the reviewer</h3><pre>' +
                     html.escape(json.dumps(row['rubric_target'], indent=2)) + '</pre>')
        parts.append('<details><summary>Attributed original source messages</summary>')
        for message in row['original_user_sources'] or []:
            parts.append('<p><b>' + html.escape(str(message['index']) + ': ' + message['author']) +
                         '</b> ' + html.escape(message['text']) + '</p>')
        parts.append('</details><details><summary>Generating policy context (fallible)</summary><pre>' +
                     html.escape(row['source_material']) + '</pre></details></article>')
    parts.append('</html>')
    destination.write_text('\n'.join(parts) + '\n')


def generate(root: Path) -> dict:
    directory = root / 'artifacts/human_review'
    packet_path = directory / 'packet.json'
    report = {"status": "packet_outputs_pending", "human_ratings": "not_supplied",
              "analysis_source_sha256": checksum(Path(__file__)),
              "qualification": "Descriptive reporting extension; no condition-effect claim, automatic adjudication or model-generated human ratings. Blank cells remain missing; NA is a separate agreement category. Family bootstrap retains paired worlds, conditions and rubric items. Kappa is undefined when expected agreement is one."}
    status_path = directory / 'status.json'
    packet_status = json.loads(status_path.read_text()) if status_path.exists() else {}
    if packet_status.get('status') == 'pending_complete_packet':
        report['available_outputs'] = packet_status['available_outputs']
        report['packet_status_sha256'] = checksum(status_path)
    if packet_path.exists() and packet_status.get('status') != 'pending_complete_packet':
        packet = json.loads(packet_path.read_text())
        identities = {row['id'] for row in packet}
        if len(packet) != 120 or len(identities) != 120:
            raise ValueError('Expected the complete fixed 120-output packet')
        key_path = directory / 'condition_key_private.json'
        key = json.loads(key_path.read_text())
        if set(key) != identities:
            raise ValueError('Private cluster key differs from blinded packet')
        render_packet(packet, directory / 'packet.html')
        paths = [directory / f'rater_{i}.csv' for i in (1, 2)]
        ratings = [read_ratings(path, identities) for path in paths]
        records = []
        supplied = [sum(bool(row[item]) for row in rater.values() for item in ITEMS) for rater in ratings]
        for identity in sorted(identities):
            for item in ITEMS:
                a, b = [rater.get(identity, {}).get(item, '') for rater in ratings]
                if a and b:
                    records.append({'id': identity, 'item': item, 'a': a, 'b': b,
                                    'family': key[identity]['family_id']})
        report.update(status='ratings_complete_adjudication_pending' if supplied == [1200, 1200] else 'packet_ready_ratings_pending',
                      human_ratings='partial_or_complete_actual_annotations' if any(supplied) else 'not_supplied',
                      outputs=120, ratings_supplied_by_rater=supplied, required_ratings_per_rater=1200,
                      inputs={str(path.relative_to(root)): checksum(path) for path in [packet_path, key_path, *paths] if path.exists()})
        if records:
            report['overall'] = {**agreement([(r['a'], r['b']) for r in records]), **cluster_intervals(records)}
            report['per_item'] = {}
            for item in ITEMS:
                selected = [r for r in records if r['item'] == item]
                report['per_item'][item] = {**agreement([(r['a'], r['b']) for r in selected]), **cluster_intervals(selected)}
        disagreements = [{k: v for k, v in row.items() if k != 'family'} for row in records if row['a'] != row['b']]
        # Preserve independent originals. Adjudication is a separate human action.
        (directory / 'disagreements.json').write_text(json.dumps(disagreements, indent=2) + '\n')
        report['disagreements'] = len(disagreements)
    output = root / 'reports/tables/human_review_status.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'human_ratings')}))
    return report


if __name__ == '__main__':
    generate(Path(__file__).resolve().parents[1])
