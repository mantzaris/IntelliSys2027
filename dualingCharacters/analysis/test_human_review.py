"""Synthetic unit fixtures only; never exported as human annotations."""
import csv
import json
import pytest
from human_review import ITEMS, agreement, cluster_intervals, generate, read_ratings, render_packet


def test_missing_and_invalid_ratings_are_not_silent_annotations(tmp_path):
    path = tmp_path / 'rater.csv'
    assert read_ratings(path, {'P0001'}) == {}
    with path.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id', *ITEMS, 'comments'])
        writer.writerow(['P0001', *([''] * 10), ''])
    assert all(read_ratings(path, {'P0001'})['P0001'][item] == '' for item in ITEMS)
    path.write_text(path.read_text().replace('P0001', 'P0002'))
    with pytest.raises(ValueError, match='Unknown or duplicate'):
        read_ratings(path, {'P0001'})


def test_agreement_degenerate_cases_and_family_uncertainty():
    assert agreement([])['raw_agreement'] is None
    assert agreement([('1', '1')])['cohen_kappa'] is None
    assert agreement([('1', '1'), ('0', '0')])['cohen_kappa'] == 1
    assert agreement([('1', '0'), ('0', '1')])['cohen_kappa'] == -1
    records = [{'family': 'a', 'a': '1', 'b': '1'}, {'family': 'b', 'a': '0', 'b': '1'}]
    result = cluster_intervals(records, draws=200)
    assert result['family_clusters'] == 2
    assert result['raw_agreement_ci95'] == [0., 1.]


def test_reviewer_render_escapes_outputs_and_never_uses_condition_key(tmp_path):
    destination = tmp_path / 'packet.html'
    render_packet([{'id': 'P0001', 'response': '<script>bad()</script>',
                    'rubric_target': {}, 'source_material': '{}',
                    'original_user_sources': [{'index': 1, 'author': 'user', 'text': '<update>'}]}], destination)
    output = destination.read_text()
    assert '<script>' not in output
    assert '&lt;script&gt;' in output
    assert 'condition_key' not in output


def test_empty_legacy_packet_stays_pending(tmp_path):
    directory = tmp_path / 'artifacts/human_review'
    directory.mkdir(parents=True)
    (tmp_path / 'reports/tables').mkdir(parents=True)
    (directory / 'packet.json').write_text('[]')
    (directory / 'status.json').write_text(json.dumps({'status': 'pending_complete_packet', 'available_outputs': 0}))
    report = generate(tmp_path)
    assert report['status'] == 'packet_outputs_pending'
    assert report['human_ratings'] == 'not_supplied'
    assert not (directory / 'packet.html').exists()
