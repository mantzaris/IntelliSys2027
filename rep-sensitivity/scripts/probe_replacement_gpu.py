"""Bounded hardware probe. Its shortened outputs are never study observations.

Use fixed, previously collected development prompts to measure whether the
frozen BF16 model can run on the replacement GPU without quantizing weights.
Charge loading and inference to the existing cumulative additional-work ledger.
"""
import argparse
import fcntl
import gzip
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json, utcnow
from run_objective_confirmation import append, prior_seconds


def requests(config):
    root = Path(config['source_calls'])
    rows = []
    for entry in config['requests']:
        path = root / (entry['request_hash'] + '.json.gz')
        with gzip.open(path, 'rt') as handle:
            row = json.load(handle)
        if digest(row['prompt']) != entry['prompt_sha256']:
            raise RuntimeError('Development prompt changed')
        rows.append(row)
    return rows


def worker(config):
    os.environ.update(HF_HUB_DISABLE_XET='1', VLLM_NO_USAGE_STATS='1', DO_NOT_TRACK='1')
    from datetime import datetime
    from vllm import LLM, SamplingParams
    from vllm.sampling_params import GuidedDecodingParams
    from rep_sensitivity.policies import OUTPUT_SCHEMA, MANAGER_OUTPUT_SCHEMA

    rows = requests(config)
    source = rows[0]['settings']
    for field, value in [('engine_version', '0.10.2'), ('precision', 'bfloat16'),
                         ('quantization', None), ('batch_size', 32)]:
        if source[field] != value:
            raise RuntimeError('Unexpected frozen model setting: ' + field)
    if (digest(OUTPUT_SCHEMA) != source['output_schema_sha256'] or
            digest(MANAGER_OUTPUT_SCHEMA) != source['manager_output_schema_sha256']):
        raise RuntimeError('Response contract differs from source requests')
    path = Path('artifacts/models/qwen3_path.txt').read_text().strip()
    metadata = json.loads(Path('records/models/qwen3.json').read_text())
    if metadata['revision'] != source['revision'] or Path(path).name != source['revision']:
        raise RuntimeError('Wrong model snapshot')
    load_start = time.monotonic()
    engine = LLM(model=path, tokenizer=path, dtype='bfloat16',
        max_model_len=config['max_model_len'], gpu_memory_utilization=0.92,
        enforce_eager=False, max_num_seqs=32, enable_prefix_caching=False,
        seed=1729, trust_remote_code=False, cpu_offload_gb=config['cpu_offload_gb'])
    loaded_seconds = time.monotonic() - load_start
    tokenizer = engine.get_tokenizer()
    if digest(tokenizer.chat_template) != source['chat_template_sha256']:
        raise RuntimeError('Chat template changed')
    tokens = []
    params = []
    for row in rows:
        prompt = tokenizer.apply_chat_template([{'role': 'user', 'content': row['prompt']}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False,
            strftime_now=lambda fmt: datetime(2026, 10, 16).strftime(fmt))
        ids = tokenizer.encode(prompt, add_special_tokens=False)
        if len(ids) + config['probe_output_cap'] > config['max_model_len']:
            raise RuntimeError('Probe would truncate input')
        tokens.append(ids)
        params.append(SamplingParams(temperature=source['temperature'], top_p=source['top_p'],
            seed=row['seed'], max_tokens=config['probe_output_cap'],
            guided_decoding=GuidedDecodingParams(json=OUTPUT_SCHEMA if row['stage'] == 'root' else MANAGER_OUTPUT_SCHEMA)))
    started = time.monotonic()
    outputs = engine.generate([{'prompt_token_ids': ids} for ids in tokens], params, use_tqdm=False)
    elapsed = time.monotonic() - started
    counts = [len(out.outputs[0].token_ids) for out in outputs]
    result = {'utc': utcnow(), 'config_sha256': digest(config), 'load_seconds': loaded_seconds,
        'batch_seconds': elapsed, 'input_tokens': sum(map(len, tokens)), 'output_tokens': sum(counts),
        'output_tokens_per_second': sum(counts) / elapsed, 'requests': len(rows),
        'request_lengths': [len(t) for t in tokens], 'generated_lengths': counts,
        'finish_reasons': [out.outputs[0].finish_reason for out in outputs],
        'gpu': subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total,driver_version,uuid',
            '--format=csv,noheader'], text=True).strip(),
        'dependencies': {p: importlib.metadata.version(p) for p in ['vllm', 'torch', 'transformers', 'numpy', 'xgrammar']},
        'interpretation': 'Hardware compatibility and short-output throughput only. No accuracy analysis. '
            'The 64-token cap differs from research runs; do not extrapolate as a measured full-run rate.'}
    immutable_json(Path(config['record_directory']) / 'measurement.json', result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/rtx4090-probe-v1.json')
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    if args.worker:
        worker(config)
        return
    output = Path(config['record_directory'])
    if (output / 'attempt.json').exists() or (output / 'measurement.json').exists():
        raise RuntimeError('Probe already attempted; no automatic repeats')
    requests(config)
    shared = Path('artifacts/runs/objective-confirmation-execution')
    shared.mkdir(parents=True, exist_ok=True)
    lock = (shared / '.controller.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    journal = shared / 'budget.jsonl'
    events = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    remaining = 7200 - prior_seconds(events)
    allocation = config['maximum_wall_seconds']
    if remaining < allocation + config['reserve_seconds']:
        raise RuntimeError('Insufficient shared allowance after preserving reserved work')
    if subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip():
        raise RuntimeError('GPU occupied; no process interrupted')
    attempt = 'rtx4090-probe-' + str(time.time_ns())
    append(journal, {'event': 'attempt_start', 'attempt': attempt, 'experiment': config['name'],
        'reserved_seconds': allocation, 'model': 'qwen3', 'config_sha256': digest(config)})
    start = time.monotonic()
    child = subprocess.Popen([sys.executable, __file__, '--config', args.config, '--worker'], start_new_session=True)
    timeout = False
    try:
        code = child.wait(timeout=allocation - 30)
    except subprocess.TimeoutExpired:
        timeout = True
        os.killpg(child.pid, signal.SIGTERM)
        try:
            code = child.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            code = child.wait(timeout=5)
    elapsed = time.monotonic() - start
    result = {'event': 'attempt_end', 'attempt': attempt, 'experiment': config['name'],
        'elapsed_seconds': elapsed, 'returncode': code, 'wall_budget_stop': timeout}
    append(journal, result)
    immutable_json(output / 'attempt.json', {**result, 'utc': utcnow(),
        'cumulative_additional_seconds': prior_seconds(events) + elapsed})
    raise SystemExit(code)


if __name__ == '__main__':
    main()
