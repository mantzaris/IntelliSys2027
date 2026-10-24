"""Checks for presentation changes introduced after the scientific freeze."""
import re
import pytest
from supplements.exploration_003.common import HERE
from .prepare_review import reviewer_codebook,preserve_or_write
from .verify_package import paired_means


def test_reviewer_rubric_has_no_condition_or_character_labels():
    text=reviewer_codebook((HERE/'CODEBOOK.md').read_text())
    assert not re.search(r'\b(?:C[1-6]|A[1-3]|Jekyll|Hyde|Rival|Traditionalist|Provocateur)\b',text)
    assert 'unsupported_recollection' in text and 'source_based_correction' in text
    assert 'Coherence0–2' in text and 'Substantive novelty0–2' in text


def test_presentation_version_cannot_overwrite_changed_content(tmp_path):
    path=tmp_path/'item.txt'
    preserve_or_write(path,'same item identity')
    preserve_or_write(path,'same item identity')
    with pytest.raises(ValueError):preserve_or_write(path,'changed identity')
    assert path.read_text()=='same item identity'


def test_reporting_cannot_hide_duplicate_or_missing_worlds():
    a={'family_id':'f','world':'authorized','value':3}
    b={'family_id':'f','world':'hypothetical','value':1}
    assert paired_means([a,b],'value')=={'f':2}
    with pytest.raises(ValueError):paired_means([a,a,b],'value')
    with pytest.raises(ValueError):paired_means([a],'value')
