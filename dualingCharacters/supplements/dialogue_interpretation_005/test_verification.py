"""Small checks for reviewer isolation and offline evidence navigation."""
import pytest
from .verification import no_private_keys,Links
from .annotations import RESPONSES
from .blinding import anonymize

def test_nested_role_metadata_is_not_reviewer_evidence():
    value={'inbox':[{'sender_role':'Hyde','claim':'Robin recommends Tuesday.'}],'seed':29}
    safe=anonymize(value,{'Robin':'Speaker 1'})
    no_private_keys(safe)
    assert safe['inbox'][0]['claim']=='Speaker 1 recommends Tuesday.'
    with pytest.raises(AssertionError):no_private_keys(value)

def test_missing_followup_stays_distinct_from_semantic_response():
    assert 'missing follow-up' in RESPONSES and 'ignored' not in RESPONSES
    value={'visible':None,'next_recipient_opportunity':None,'next_response':'missing_opportunity'}
    assert anonymize(value,{})==value

def test_offline_checker_detects_external_and_broken_destinations():
    p=Links();p.feed('<div id="known"></div><a href="#unknown">source</a><img src="https://example.invalid/pixel">')
    assert p.remote and p.links[0][1:] not in p.ids


def test_blinding_does_not_rewrite_authority_or_api_meaning():
    x={'kind':'recollect','claim':'I propose Tuesday; Robin has not approved it.'}
    assert anonymize(x,{'Robin':'Speaker 1'})=={'kind':'recollect','claim':'I propose Tuesday; Speaker 1 has not approved it.'}
