"""Rebuild the bounded, exploratory interpretation of the original raw pilot."""
import json
from rep_sensitivity.pilot_interpretation import summarize

if __name__ == '__main__':
    result = summarize('artifacts/runs/pilot-v7', 'results/pilot-interpretation-v2')
    focus = [r for r in result['comparisons'] if r['dimension'] == 'overall'
             and r['kind'] == 'schedule' and r['organization'] == 'hierarchical']
    print(json.dumps({'base_pairs': result['base_pairs'], 'trajectories': result['trajectories'], 'focus': focus}))
