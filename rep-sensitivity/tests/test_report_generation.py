"""Incomplete analyses must never appear as completed manuscript results."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


class ReportGenerationTests(unittest.TestCase):
    def test_completedness_guard_and_numeric_traceability(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d);(dest/'manuscript').mkdir();(dest/'records').mkdir()
            (dest/'manuscript/abstract-development.tex').write_text((root/'manuscript/abstract-development.tex').read_text())
            result=dest/'results/main-v7/analysis.json';result.parent.mkdir(parents=True)
            result.write_text(json.dumps({'suite':'main-v7','complete':False}))
            def build():subprocess.run([sys.executable,str(root/'scripts/build_study_report.py')],cwd=dest,check=True,capture_output=True)
            build()
            self.assertNotIn(r'\begin{table}',(dest/'manuscript/generated/main-results.tex').read_text())
            self.assertFalse(json.loads((dest/'records/study-report-status.json').read_text())['submission_ready'])
            # Synthetic fixture only; never stored among empirical project outputs.
            rows=[];contrasts=[]
            for kind in ('schedule','workflow'):
                for model in ('qwen3','phi4'):
                    for org in ('flat','hierarchical'):
                        for policy in ('ordinary','checklist','scope'):
                            for condition in ('single','exact','paraphrase'):
                                rows.append(dict(kind=kind,model=model,organization=org,policy=policy,condition=condition,accuracy=0.75))
                for model in ('qwen3','phi4','equal_model_average'):
                    for contrast in ('H1_exact','H1_paraphrase','H2','H3','H4_error','H4_retention'):
                        contrasts.append(dict(kind=kind,model=model,contrast=contrast,estimate=-0.125,lower=-0.25,upper=0.0,clusters=48,degenerate_bootstrap=False))
            result.write_text(json.dumps(dict(suite='main-v7',complete=True,summary=rows,contrasts=contrasts)))
            build()
            text=(dest/'manuscript/generated/main-results.tex').read_text()
            self.assertIn('-12.5 [-25.0, 0.0]',text)
            self.assertIn('75.0',text)
            trace=json.loads((dest/'manuscript/generated/study_numerical_traceability.json').read_text())
            self.assertTrue(all(r['record'] in rows+contrasts for r in trace))
            abstract=(dest/'manuscript/generated/abstract.tex').read_text()
            words=re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*",abstract)
            self.assertTrue(150<=len(words)<=250,len(words))
            status=json.loads((dest/'records/study-report-status.json').read_text())
            self.assertEqual(status['pending_analysis_stages'],['supporting-v7','live-v8'])
            self.assertFalse(status['submission_ready'])
