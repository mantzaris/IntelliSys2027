"""Manuscript updates must preserve prose and never publish incomplete evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import manuscript_content as mc
import build_manuscript as bm


class ReportGenerationTests(unittest.TestCase):
    def test_prose_and_bibliography_survive_repeated_updates(self):
        original="Authored introduction.\n% BEGIN AUTO: result\nPending.\n% END AUTO: result\n"+r"\begin{thebibliography}{1}\bibitem{x} Source.\end{thebibliography}"
        changed=mc.replace_block(original,'result','Accuracy: 75 percent.')
        self.assertTrue(changed.startswith('Authored introduction.'))
        self.assertEqual(original.split(r'\begin{thebibliography}')[1],changed.split(r'\begin{thebibliography}')[1])
        self.assertEqual(mc.replace_block(changed,'result','Accuracy: 75 percent.'),changed)
        with self.assertRaises(ValueError):mc.replace_block(changed,'absent','new')
        with self.assertRaises(ValueError):mc.replace_block(changed+'\n% BEGIN AUTO: result','result','new')

    def test_incomplete_heldout_has_no_manuscript_estimates(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);p=root/'results/main-v7/analysis.json';p.parent.mkdir(parents=True)
            p.write_text(json.dumps({'complete':False,'summary':[{'accuracy':.987654}]}))
            with patch.object(mc,'ROOT',root),patch.object(bm,'ROOT',root):
                self.assertIsNone(mc.completed('main-v7'))
                self.assertEqual(bm.future_results(),('','',''))

    def test_completed_heldout_contrast_sign_and_denominators(self):
        # Synthetic fixture remains temporary, outside empirical result folders.
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);p=root/'results/main-v7/analysis.json';p.parent.mkdir(parents=True)
            rows=[];contrasts=[]
            for kind in ('schedule','workflow'):
                for model in ('qwen3','phi4'):
                    for org in ('flat','hierarchical'):
                        for policy in ('ordinary','checklist','scope'):
                            for condition in ('single','exact','paraphrase'):
                                rows.append(dict(model=model,kind=kind,organization=org,policy=policy,
                                    condition=condition,n=8,correct=6,clusters=2,accuracy=.75))
                    for contrast in ('H1_exact','H1_paraphrase','H2','H3','H4_error','H4_retention'):
                        contrasts.append(dict(model=model,kind=kind,contrast=contrast,estimate=-.125,lower=-.25,upper=0,clusters=2))
            p.write_text(json.dumps(dict(complete=True,summary=rows,contrasts=contrasts)))
            with patch.object(mc,'ROOT',root),patch.object(bm,'ROOT',root):
                main,_,appendix=bm.future_results()
            self.assertIn('-12.50 [-25.00, +0.00]',main)
            self.assertIn('75.00',main)
            self.assertIn('2 & 24',main)  # 2 bases, 24 trajectories/arm.
            self.assertIn('Positive H1 values indicate harm',main)
            self.assertIn(r'H4\_retention',main)
            self.assertIn('Held-Out Workflow Results',appendix)

    def test_external_fragments_and_missing_figures_rejected(self):
        base=r'\begin{thebibliography}{1}\end{thebibliography}'
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            for command in (r'\input{section}',r'\include{section}',r'\bibliography{refs}',r'\includegraphics{../plot.pdf}'):
                with self.assertRaises(ValueError):mc.validate_single_source(base+command,root)
            (root/'plot.pdf').write_bytes(b'fixture')
            mc.validate_single_source(base+r'\includegraphics{plot.pdf}',root)

    def test_worked_example_with_both_independent_checkers(self):
        result=bm.checked_example()
        self.assertEqual(result['1']['answer'],'Q')
        self.assertEqual(result['2']['answer'],'P')
        self.assertFalse(result['1']['candidates']['P']['feasible'])
        self.assertEqual(result['2']['candidates']['P']['objective'],3)
