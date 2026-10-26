"""Synthetic display fixtures; no research annotations generated."""
import pytest
from supplements.results_clarity_007.review_package import response

def turn():
 return {'turn':5,'action':{'actor':'Speaker 1','kind':'peer','opportunity':4,'claim':'SYNTHETIC sender statement','observation':{'sources':[]}},'defender':{'raw':'{"plan":["SYNTHETIC recipient output"]}'},'defender_observation':{'sources':[]}}

def test_answerer_recipient_renders_answer_not_same_turn_sender():
 text=response(turn(),'answerer','First following opportunity')
 assert 'SYNTHETIC recipient output' in text
 assert 'SYNTHETIC sender statement' not in text
 assert 'Actual answerer observation' in text

def test_component_recipient_keeps_actual_component_output():
 text=response(turn(),'component','First following opportunity')
 assert 'SYNTHETIC sender statement' in text and 'SYNTHETIC recipient output' not in text

def test_missing_followup_does_not_create_ignored_label():
 text=response(None,'component','First following opportunity')
 assert 'no recorded opportunity' in text and 'ignored' not in text
