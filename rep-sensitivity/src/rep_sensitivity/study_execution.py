"""Sequential study stages with prospective freezes and no outcome-based stopping."""
import importlib.metadata
import json
from pathlib import Path
import shutil
from .analysis import summarize
from .aux_analysis import summarize as summarize_aux
from .gates import qualify
from .live import run_live
from .mutations import describe
from .planning import project
from .replay import prepare,run
from .schema import digest
from .storage import immutable_json,utcnow
from .supporting import run_controls

FROZEN=Path('configs/frozen')


def complete(name,alias,kind='replay'):
    root=Path('artifacts/runs')/name;model=root/alias
    events=model/'events.jsonl'
    if not events.exists():return False
    if not any(json.loads(line)['event']=='run_complete' for line in events.read_text().splitlines()):return False
    scores=list((model/'scores').glob('*.json'))
    if kind=='replay':
        manifest=json.loads((root/'manifest.json').read_text());config=manifest['config']
        expected=manifest['manager_calls']//len(config['models'])
        if len(scores)!=config['base_pairs']:return False
    elif kind=='controls':
        manifest=json.loads((model/'run-manifest.json').read_text());expected=manifest['calls']
        if len(scores)!=manifest['trajectories']:return False
    else:
        manifest=json.loads((root/'manifest.json').read_text())
        if len(scores)!=manifest['trajectories']:return False
        expected=sum(json.loads(p.read_text())['calls'] for p in scores)
    return len(list((model/'calls').glob('*.json.gz')))==expected


def read(path):return json.loads(Path(path).read_text())


def publish(config,reason,evidence):
    FROZEN.mkdir(parents=True,exist_ok=True)
    path=FROZEN/(config['name']+'.json')
    record=Path('records/freezes')/(config['name']+'.json')
    if record.exists():
        if read(record)['config_sha256']!=digest(config):raise RuntimeError('Attempt to change a frozen configuration')
    else:
        immutable_json(record,{'frozen_utc':utcnow(),'config_sha256':digest(config),'reason':reason,'evidence':evidence,
                              'source_sha256':digest({p.name:p.read_text() for p in Path(__file__).parent.glob('*.py')}),
                              'registration':'Prospective repository freeze, not an external preregistration registry'})
    immutable_json(path,config)
    return config


def freeze_validation(templates):
    path=FROZEN/'validation-v7.json'
    if path.exists():return read(path)
    if not complete('pilot-v7','qwen3'):raise RuntimeError('Full pilot is not complete')
    gates={}
    for alias in ('qwen3','mistral24'):
        a=read(Path('records/gates')/('competence-'+alias+'-v7.json'))
        b=read(Path('records/gates')/('summary-smoke-'+alias+'-v7.json'))
        if not a['passed'] or not b['contract_valid']:raise RuntimeError('Selected model is not qualified: '+alias)
        gates[alias]={'competence':a,'summary':b}
    config=read(Path(templates)/'validation-candidate-v7.json')
    config.update(name='validation-v7',status='frozen_validation',freeze_required=False)
    pilot=summarize('artifacts/runs/pilot-v7','results/pilot-v7')
    if not pilot['complete']:raise RuntimeError('Pilot has incomplete clusters')
    return publish(config,'Completed development pilot and qualified model families',
                   {'development_gates':gates,'pilot_analysis_sha256':digest(pilot)})


def freeze_main(templates):
    if (FROZEN/'main-v7.json').exists():return read(FROZEN/'main-v7.json')
    if not all(complete('validation-v7',m) for m in ('qwen3','mistral24')):
        raise RuntimeError('Both complete validation models are required before held-out inference')
    validation=summarize('artifacts/runs/validation-v7','results/validation-v7')
    if not validation['complete']:raise RuntimeError('Validation has incomplete clusters')
    rule=read(Path(templates)/'allocation-rule-v1.json')
    primary=[r for r in validation['competence'] if r['kind']=='schedule']
    if len(primary)!=2 or any(r['accuracy']<rule['primary_validation_competence_threshold'] for r in primary):
        raise RuntimeError('Primary validation competence is inadequate; held-out execution remains blocked')
    candidate=read(FROZEN/'validation-v7.json')
    projections={}
    for n in (rule['preferred_heldout_base_pairs'],rule['reduced_heldout_base_pairs']):
        target={**candidate,'base_pairs':n}
        projections[str(n)]=project('artifacts/runs/validation-v7',target)
        if projections[str(n)]['projected_total_inference_hours'] is None:raise RuntimeError('Missing measured resource cells')
    preferred=rule['preferred_heldout_base_pairs']
    n=rule['reduced_heldout_base_pairs'] if projections[str(preferred)]['projected_total_inference_hours']>rule['main_inference_planning_threshold_hours'] else preferred
    candidate.update(name='main-v7',status='frozen_heldout',split='heldout',base_pairs=n,
                     expected_trajectories=144*n,expected_manager_calls=288*n)
    validation_bytes=sum(p.stat().st_size for p in Path('artifacts/runs/validation-v7').glob('*/calls/*.json.gz'))
    projected_bytes=int(validation_bytes*n/36*2+100_000_000)
    free=shutil.disk_usage('.').free
    if free<projected_bytes:raise RuntimeError('Insufficient local pod storage for conservative artifact projection')
    evidence={'allocation_rule':rule,'validation_analysis_sha256':digest(validation),'projections':projections,
              'available_storage_bytes':free,'projected_artifact_bytes_with_margin':projected_bytes,
              'secondary_competence':[r for r in validation['competence'] if r['kind']=='workflow']}
    manifest,pairs,corpus=prepare(candidate,Path('artifacts/runs/main-v7'))
    immutable_json(Path('artifacts/runs/main-v7/mutation-records-v1.json'),[describe(p) for p in pairs.values()])
    common={k:candidate[k] for k in ('models','model_settings','max_context_tokens','max_output_tokens','temperature','top_p',
                                    'batch_size','enforce_eager','gpu_memory_utilization','root_ancestry_registry')}
    supporting=read(Path(templates)/'supporting-provisional.json')
    supporting.update(common,name='supporting-v7',status='frozen',source_corpus='artifacts/runs/main-v7',
                      pair_indices=rule['supporting_pair_indices'],stochastic_repetitions=rule['supporting_stochastic_repetitions'],
                      bootstrap_strata=rule['supporting_bootstrap_strata'])
    publish(supporting,'Targeted controls fixed before main inference',{'allocation_rule_sha256':digest(rule)})
    live=read(Path(templates)/'live-provisional.json')
    live.update(common,name='live-v7',status='frozen',benchmark_version=2,generated_pairs=rule['live_generated_pairs'],
                worlds=rule['live_worlds'],stochastic_repetitions=rule['live_stochastic_repetitions'],
                bootstrap_strata=rule['live_bootstrap_strata'])
    publish(live,'New live instances and token allowance fixed before main inference',{'allocation_rule_sha256':digest(rule)})
    # Publish the main launch marker last so a crash cannot leave missing companion protocols.
    publish(candidate,'Fixed sample allocation from complete validation; no held-out outcomes inspected',evidence)
    return candidate


def development_extensions(alias,templates,model=None):
    common=read(Path(templates)/'validation-candidate-v7.json')
    settings={k:common[k] for k in ('models','model_settings','max_context_tokens','max_output_tokens','temperature','top_p',
                                   'batch_size','enforce_eager','gpu_memory_utilization','root_ancestry_registry')}
    controls=read(Path(templates)/'supporting-provisional.json')
    controls.update(settings,name='controls-development-v7',status='development_controls',
                    source_corpus='artifacts/runs/pilot-v7',pair_indices=[0,5],stochastic_repetitions=1,
                    bootstrap_strata=['decision_changed'])
    if not complete(controls['name'],alias,'controls'):model=run_controls(controls,alias,model)
    live=read(Path(templates)/'live-provisional.json')
    live.update(settings,name='live-development-v7',status='development_live',benchmark_version=2,
                generated_pairs=1,worlds=[0],stochastic_repetitions=2)
    if not complete(live['name'],alias,'live'):model=run_live(live,alias,model)
    return model


def execute_stage(stage,templates):
    for package,version in (('vllm','0.10.2'),('transformers','4.55.4')):
        if importlib.metadata.version(package)!=version:raise RuntimeError('Inference environment changed: '+package)
    if stage=='mistral_validation':
        model=qualify('mistral24',templates)
        config=freeze_validation(templates)
        model=development_extensions('mistral24',templates,model)
        if not complete(config['name'],'mistral24'):run(config,'mistral24',model=model)
        return
    alias='qwen3' if stage=='qwen_main' else 'mistral24'
    model=None
    if alias=='qwen3':
        model=development_extensions(alias,templates,model)
        validation=read(FROZEN/'validation-v7.json')
        if not complete(validation['name'],alias):model=run(validation,alias,model=model)
    config=freeze_main(templates)
    if not complete(config['name'],alias):model=run(config,alias,model=model)
    controls=read(FROZEN/'supporting-v7.json')
    if not complete(controls['name'],alias,'controls'):model=run_controls(controls,alias,model)
    live=read(FROZEN/'live-v7.json')
    if not complete(live['name'],alias,'live'):run_live(live,alias,model)
    if all(complete('main-v7',m) for m in ('qwen3','mistral24')):
        summarize('artifacts/runs/main-v7','results/main-v7')
        for name in ('supporting-v7','live-v7','controls-development-v7','live-development-v7'):
            summarize_aux(Path('artifacts/runs')/name,Path('results')/name)
