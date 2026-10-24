"""One CPU command regenerates the separate evidence package from eligible artifacts."""
import argparse
import importlib
import subprocess
import sys
from .common import ROOT,HERE,REPORTS,ARTIFACTS,read,write,utc,reporting_environment
from pcc.resources import sha256


def main():
    if (HERE/'FREEZE.json').exists():
        from .freeze import verify
        verify()
    subprocess.run([sys.executable,'-m','supplements.long_horizon_intent_002.operations','update'],cwd=ROOT,env=reporting_environment(),check=True)
    modules=('core_audit','clarification_exposure','training_situations','core_horizons','trajectory_analysis','source_dynamics','illustrations','legacy_packets','figures')
    for module in modules:importlib.import_module('supplements.long_horizon_intent_002.'+module).main()
    from .budget import readiness
    from .freeze import checkpoint_readiness
    from .human_review import prepare,score
    readiness();checkpoint_readiness();prepare();score()
    from .report import main as report
    report()
    from .draft import main as draft
    draft()
    sources={str(p.relative_to(ROOT)):sha256(p) for p in sorted(HERE.glob('*.py'))}
    manifests={str(p.relative_to(ROOT)):sha256(p) for p in sorted(REPORTS.glob('*provenance.json'))}
    for name in ('TEXT_PROVENANCE.json','INTENT_FIGURE_MANIFEST.json','FIGURE_MANIFEST.json','DATASET_AUDIT.json','OVERLAP_AUDIT.json','TOKEN_FEASIBILITY.json','INTENT_READINESS.json','CHECKPOINT_READINESS.json','DRAFT_STATUS.json','HUMAN_REVIEW_STATUS.json','LEGACY_HUMAN_PACKET_STATUS.json','INTENT_SCORES.json','TESTS.json'):
        p=REPORTS/name
        if p.exists():manifests[str(p.relative_to(ROOT))]=sha256(p)
    write(REPORTS/'PROVENANCE.json',{'generated_utc':utc(),'source_hashes':sources,'analysis_manifests':manifests,
      'core_freeze_sha256':sha256(ROOT/'configs/freeze.json'),'review_freeze_sha256':sha256(ROOT/'supplements/review_001/FREEZE.json'),
      'intent_freeze_sha256':sha256(HERE/'FREEZE.json') if (HERE/'FREEZE.json').exists() else None,'dataset_manifest_sha256':sha256(HERE/'dataset_manifest.json'),
      'reproduction_command':'PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.regenerate',
      'new_gpu_calls_in_regeneration':0,'policy_inputs_from_private_ledgers':False,
      'qualification':'Every aggregate links through its manifest to completed raw traces, fixed adapters, configurations and deterministic code. Missing fresh outputs/ratings remain pending. Core and supplementary estimates remain separate.'})


if __name__=='__main__':main()
