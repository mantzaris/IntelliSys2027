"""Readable held-out screening report, preserving failures and exact supports."""
from .report_helpers import *
def main():
 rows=read(HERE/'reports/HOLDOUT_CALIBRATION.json');assert len(rows)==14,'Wait for both complete judge runs'
 out=['# Held-out judge calibration\n','These are 80 synthetic controls per judge, separated from 40 development controls by template family. The controls share compositional grammar; performance does not validate natural research dialogues. One shared development prompt revision was made and frozen before these outputs. No human annotations were collected.\n','Abstentions, invalid spans and missing outputs count as failures in unconditional/balanced accuracy. Coverage requires a substantive answer. Zero denominators are unavailable. Screening: binary balanced accuracy ≥85% and coverage ≥80%, ≥8 positive and negative controls; categorical exact accuracy ≥85% and coverage ≥80%.\n']
 table=[]
 for r in rows:
  score=r['balanced_accuracy_abstention_as_failure'] if r['balanced_accuracy_abstention_as_failure'] is not None else r['unconditional_accuracy']
  table.append([r['model'],r['dimension'],str(r['class_support']),f"{r['correct']}/{r['binary_or_substantive_support']}",percent(score),f"{r['substantive_predictions']}/{r['binary_or_substantive_support']}",str(r['invalid_or_missing']),'pass' if r['screen_pass'] else 'fail'])
 out+=[markdown_table(['Judge','Dimension','Expected supports','Correct / eligible','Screen statistic','Substantive / eligible','Missing/invalid (all 80)','Screen'],table)]
 for r in rows:
  uncertain=(f"{r['expected_uncertain_correct']}/{r['expected_uncertain_n']}" if r['expected_uncertain_n'] else 'unavailable (no expected-uncertain controls)')
  out +=['## '+r['model']+' · '+r['dimension']+'\n',markdown_table(['Expected','Observed','Count'],[[c['expected'],c['observed'],c['count']] for c in r['confusion']]),f"Expected-uncertain responses correct: {uncertain}. Conditional accuracy among substantive responses: {percent(r['conditional_accuracy'])}; unconditional accuracy: {percent(r['unconditional_accuracy'])}. The conditional figure cannot replace the unconditional screen.\n"]
 out+=['## Interpretation limits\n','A passing dimension is screened on these templates only. Failing dimensions remain in the released raw labels and sensitivity tables, but cannot support a calibrated semantic prevalence claim. Model agreement is not truth, and a correctly quoted span is not proof of a correct reading. Fixed-event examples, the broad archive sample, and the compatibility sample have distinct denominators.\n']
 (HERE/'JUDGE_CALIBRATION.md').write_text('\n'.join(out))
 short=[]
 for dim in [r['dimension'] for r in rows if r['model']=='phi']:
  cells=[]
  for model in ['phi','qwen']:
   r=next(r for r in rows if r['model']==model and r['dimension']==dim);score=r['balanced_accuracy_abstention_as_failure'] if r['balanced_accuracy_abstention_as_failure'] is not None else r['unconditional_accuracy'];cells +=[percent(score),f"{r['substantive_predictions']}/{r['binary_or_substantive_support']}",'P' if r['screen_pass'] else 'F']
  short.append([dim.replace('_',' '),*cells])
 (HERE/'paper/calibration_table.tex').write_text(latex_table(['Dimension','Phi score','Coverage','Screen','Qwen score','Coverage','Screen'],short,'lrrrrrr')+'\n')
 print('Held-out calibration report generated, including every failure')
if __name__=='__main__':main()
