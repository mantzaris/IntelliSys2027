"""Plot actual optimizer logs from exposure-verified completed fits only."""
from collections import defaultdict
from pathlib import Path
import math
import statistics
from pcc.resources import sha256
from supplements.review_001.common import stream, write_csv
from .common import ROOT, OUT, read, write
from .plots import plt, finish


def main():
    exposures = read(OUT / 'supervision_exposure.json')
    summaries = []; series = []; inputs = [OUT / 'supervision_exposure.json']
    for fit in exposures:
        if fit['status'] != 'reconstructed_and_verified': continue
        path = ROOT / f'artifacts/runs/{fit["run_id"]}/training/loss.jsonl'
        points = list(stream(path)); inputs.append(path)
        assert len(points) == fit['optimizer_steps_in_process']
        assert len({p['step'] for p in points}) == len(points)
        assert all(math.isfinite(p['loss']) and p['loss'] >= 0 for p in points)
        assert sum(p['supervised_tokens'] for p in points) == fit['supervised_target_tokens']
        rnd = 1 if '-r1-' in fit['run_id'] else 0
        prefix = {k: fit[k] for k in ('run_id','model','condition','seed')}; prefix['round'] = rnd
        summaries.append({**prefix, 'steps_logged':len(points), 'loss_first_32_mean':statistics.mean(p['loss'] for p in points[:32]),
          'loss_last_32_mean':statistics.mean(p['loss'] for p in points[-32:]), 'zero_loss_steps':sum(p['loss']==0 for p in points),
          'nonzero_gradient_steps':sum(p['gradient_norm']>0 for p in points), 'loss_log_sha256':sha256(path)})
        for start in range(0,len(points),16):
            block = points[start:start+16]
            series.append({**prefix,'step_first':block[0]['step'],'step_last':block[-1]['step'],
              'mean_recorded_step_loss':statistics.mean(p['loss'] for p in block),
              'supervised_target_tokens':sum(p['supervised_tokens'] for p in block),
              'input_tokens':sum(p['input_tokens'] for p in block)})
    write(OUT/'training_curve_summary.json', summaries);write_csv(OUT/'training_curve_summary.csv', summaries)
    write(OUT/'training_curve_points.json', series);write_csv(OUT/'training_curve_points.csv', series)
    models = sorted({r['model'] for r in series})
    fig, axes = plt.subplots(len(models),2,figsize=(11,3.7*len(models)),squeeze=False)
    colors = {'C1':'#1768A5','C3':'#C65B25','C4':'#3D8C62','C5':'#7E55A3','A1':'#A17B14','A2':'#426F70','A3':'#A24B69','C2':'#666666','C6':'#BB602A'}
    groups = defaultdict(list)
    for point in series: groups[point['model'], point['round'], point['condition'], point['seed']].append(point)
    for mi, model in enumerate(models):
        for rnd in (0,1):
            ax=axes[mi,rnd]
            for (m,r,c,s),values in groups.items():
                if (m,r)!=(model,rnd):continue
                ax.plot([p['step_last'] for p in values], [max(p['mean_recorded_step_loss'],1e-8) for p in values],
                  color=colors[c],linestyle={17:'-',29:'--',43:':'}[s],linewidth=1.4,label=f'{c} seed {s}')
            ax.set(yscale='log',xlabel='Optimizer step (end of 16-step block)',ylabel='Mean recorded training loss',title=f'{model.upper()} round {rnd}')
            ax.grid(axis='y',alpha=.2);ax.legend(frameon=False,fontsize=8,ncol=2)
    manifest={}
    caption='Completed exposure-verified fits only, by model, condition, round and actual seed. Arithmetic means of 16 successive recorded optimizer-step losses are shown; zero means are plotted at 1e-8. Loss reflects selected supervised tokens and does not measure test generalization or permit direct curriculum-quality comparisons. Missing fits are pending, not zero-loss runs. Exact input and target counts are in the accompanying tables.'
    finish(fig,'training_curves',caption,inputs,manifest)
    write(OUT/'TRAINING_CURVE_MANIFEST.json',manifest)
    (OUT/'TRAINING_CURVES.md').write_text('# Training curves\n\n'+caption+'\n\n[PDF](figures/training_curves.pdf) · [SVG](figures/training_curves.svg) · [PNG](figures/training_curves.png)\n')


if __name__=='__main__':main()
