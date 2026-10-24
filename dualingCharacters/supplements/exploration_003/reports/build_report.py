"""Reporting-only transforms of frozen results; no new selection or model calls."""
from collections import Counter,defaultdict
from pathlib import Path
import csv
import gzip
import json
import statistics
import numpy as np
from supplements.exploration_003.common import ROOT,HERE,REPORTS,CACHE,read,write,write_csv,sha256,stream,rank
from supplements.exploration_003.analysis import verify_science,family_interval,load_cell

def csv_rows(name):
    with (REPORTS/name).open() as f:return list(csv.DictReader(f))

def cached(cell):
    # Reporting must not silently trust an unvalidated derived cache.
    return load_cell(cell)

def main():
    verify_science();audit=read(HERE/'DATA_AUDIT.json');snapshot=read(HERE/'EVIDENCE_SNAPSHOT.json')
    reference=next(r for r in snapshot['included'] if r['run_id']=='mechanism-final-001')
    m=reference['metadata'];episodes_proposed=16*2*3*4;calls_proposed=episodes_proposed*28
    estimate=1.5*(m['gpu_reserved_seconds']-m['model_load_seconds'])*calls_proposed/m['model_calls']+3*m['model_load_seconds']
    write(REPORTS/'future_resource_estimate.json',{'status':'proposal_only_not_scheduled','source_run':m['run_id'],
        'source_status_sha256':reference['status_sha256'],'observed_reserved_seconds':m['gpu_reserved_seconds'],
        'observed_load_seconds':m['model_load_seconds'],'observed_calls':m['model_calls'],
        'proposed_families':16,'worlds':2,'seeds':[17,29,43],'conditions':4,'episodes':episodes_proposed,
        'defender_calls':episodes_proposed*16,'character_calls':episodes_proposed*12,'total_calls':calls_proposed,
        'formula':'1.5 * (observed_reserved_seconds - observed_load_seconds) * proposed_calls / observed_calls + 3 * observed_load_seconds',
        'estimated_reserved_seconds':estimate,'twice_estimate_minutes':2*estimate/60,'new_gpu_calls':0,'known_cost_usd':None})
    curves=csv_rows('coverage_curves.csv');finals=[r for r in curves if r['budget']=='12']
    primary={r['condition']:r for r in finals if r['cohort']=='primary_mechanism'}
    contrast=next(r for r in read(REPORTS/'primary_paired_contrasts.json') if r.get('budget')==12 and r['metric']=='coverage')
    costs=[];frequencies=[];validity=[];performance=[];primary_episodes={};consequences=[]
    run_costs=defaultdict(Counter)
    for cell in audit['included_cells']:
        if cell['cohort']=='historical_protocol':continue
        episodes=cached(cell);actions=[a for e in episodes for a in e['actions']]
        if cell['cohort']=='primary_mechanism' and cell['condition'] in ('C3','C5'):
            primary_episodes[cell['condition']]={(e['family_id'],e['world']):e for e in episodes}
        char_input=sum(a['input_tokens'] or 0 for a in actions);char_output=sum(a['output_tokens'] or 0 for a in actions)
        defender_input=sum(e['defender_input_tokens'] for e in episodes);defender_output=sum(e['defender_output_tokens'] for e in episodes)
        char_calls=sum(a['model_call'] for a in actions);defender_calls=sum(e['defender_calls'] for e in episodes)
        row={k:cell[k] for k in ('id','cohort','condition','seed','round','families','horizon')}
        row.update(character_calls=char_calls,defender_calls=defender_calls,
            character_input_tokens=char_input,character_output_tokens=char_output,
            defender_input_tokens=defender_input,defender_output_tokens=defender_output,
            total_rollout_tokens=char_input+char_output+defender_input+defender_output,
            character_accounting='deterministic corruption; no character LLM call' if cell['condition']=='C2' else 'recorded generation tokens including prompts/history')
        costs.append(row)
        for name,value in [('model_calls',char_calls+defender_calls),('input_tokens',char_input+defender_input),('output_tokens',char_output+defender_output)]:run_costs[cell['run_id']][name]+=value
        by_family=defaultdict(list)
        for e in episodes:by_family[e['family_id']].append(e['final_success'])
        performance.append({'id':cell['id'],'cohort':cell['cohort'],'condition':cell['condition'],'seed':cell['seed'],'round':cell['round'],
          'families':len(by_family),'paired_successes':sum(all(v) for v in by_family.values()),
          'conversation_successes':sum(e['final_success'] for e in episodes),'conversations':len(episodes),
          'qualification':'During collection with antagonists, not antagonist-free learned transfer'})
        group=Counter((a['kind'],a['communication_slot'],a['applied']) for a in actions)
        frequencies.extend({'id':cell['id'],'kind':k,'reserved_communication':s,'applied':applied,'count':n} for (k,s,applied),n in sorted(group.items(),key=str))
        group=Counter(a['validity_reason'] for a in actions)
        validity.extend({'id':cell['id'],'reason':reason,'count':n} for reason,n in sorted(group.items()))
        for field in ('contradictory_source_visible','assigned_slot_match','owned_option_match','following_option_adopted'):
            observed=[a[field] for a in actions if a[field] is not None]
            consequences.append({'id':cell['id'],'field':field,'true':sum(v is True for v in observed),
                'observed_actions':len(observed),'missing_actions':len(actions)-len(observed),
                'qualification':'Observable flag among all recorded attempts with that field; not inferred intent or causal influence'})
    reconciliation=[]
    for entry in snapshot['included']:
        if entry['run_id'] not in run_costs:continue
        totals=run_costs[entry['run_id']];meta=entry['metadata'];row={'run_id':entry['run_id'],'reserved_seconds':meta['gpu_reserved_seconds'],'load_seconds':meta.get('model_load_seconds')}
        for field in ('model_calls','input_tokens','output_tokens'):
            row['rollout_'+field]=totals[field];row['ledger_'+field]=meta[field];row['outside_rollout_'+field]=meta[field]-totals[field]
            if row['outside_rollout_'+field]<0:raise ValueError('Raw rollout accounting exceeds ledger')
            if entry['cohort']=='primary_mechanism' and row['outside_rollout_'+field]!=0:raise ValueError('Pilot accounting does not reconcile')
        row['qualification']='Main residual includes recovery candidate generation; no attempt to allocate run loading time by condition in the multi-condition mechanism pilot'
        reconciliation.append(row)
    for name,rows in [('cost_accounting.csv',costs),('run_cost_reconciliation.csv',reconciliation),('action_frequencies.csv',frequencies),('action_validity.csv',validity),('collection_performance_context.csv',performance),('observable_consequences.csv',consequences)]:write_csv(REPORTS/name,rows)

    overlap=csv_rows('primary_overlap.csv');mix=[]
    for control in ('C3','C5'):
        values=defaultdict(list)
        for r in overlap:values[r['family_id']].append(float(r['mixture_minus_'+control]))
        family_means=[statistics.mean(v) for v in values.values()]
        mix.append({'comparison':'six-plus-six minus '+control,'families':len(values),'difference':statistics.mean(family_means),'family_interval':family_interval(family_means),'qualification':'Offline prefix archive mixture, not a newly executed ensemble'})
    write(REPORTS/'mixture_paired_contrasts.json',mix)
    archive=csv_rows('archive_rarefaction.csv');whole=[]
    for condition in ('C3','C5','balanced_mixture'):
        values=[int(r['categories']) for r in archive if r['condition']==condition and r['families']=='8']
        whole.append({'condition':condition,'families':8,'worlds':16,'opportunities':192,'mean':statistics.mean(values),'minimum':min(values),'maximum':max(values),'orderings':100,'qualification':'Ordering/allocation sensitivity, not a confidence interval'})
    write(REPORTS/'whole_archive_summary.json',whole)
    archive_costs=[]
    families=sorted({f for f,w in primary_episodes['C3']})
    for ordering_id in range(100):
        ordering=sorted(families,key=lambda f:rank(f'exploration003-archive-{ordering_id}',f))
        for method in ('C3','C5','balanced_mixture'):
            character_tokens=defender_tokens=0
            for index,family in enumerate(ordering):
                selected=('C5' if index%2==0 else 'C3') if method=='balanced_mixture' else method
                for world in ('authorized','hypothetical'):
                    episode=primary_episodes[selected][family,world]
                    character_tokens+=sum(a['input_tokens']+a['output_tokens'] for a in episode['actions'])
                    defender_tokens+=episode['defender_input_tokens']+episode['defender_output_tokens']
            archive_costs.append({'ordering':ordering_id,'method':method,'families':8,'opportunities':192,
                'character_calls':192,'defender_calls':256,'character_tokens':character_tokens,
                'defender_tokens':defender_tokens,'total_tokens':character_tokens+defender_tokens})
    write_csv(REPORTS/'archive_cost_accounting.csv',archive_costs)

    # Cast compatibility is an audit of assigned adoption objectives, not a claim
    # that all coupled utility terms are simultaneously maximized.
    run=ROOT/'artifacts/runs/mechanism-final-001';goals=defaultdict(dict)
    for a in stream(run/'C5_characters.jsonl'):goals[a['family_id'],a['world']][a['actor']]=(a['assigned_slot'],a['owned_option'])
    compatibility={'episodes':len(goals),'distinct_assigned_slots':sum(len({s for s,v in g.values()})==len(g) for g in goals.values()),
       'interpretation':'Owned-option adoption objectives can be jointly satisfied in different slots. Other utility terms concern peer behavior; mutually compatible full utilities or optimized equilibrium are not established.',
       'source_sha256':sha256(run/'C5_characters.jsonl')}
    write(REPORTS/'GOAL_COMPATIBILITY.json',compatibility)

    # Reproduce the legacy repetition implementation independently of descriptors.
    legacy=[]
    for condition in ('C3','C5'):
        groups=defaultdict(list)
        for a in stream(run/f'{condition}_characters.jsonl'):
            if a['kind'] in {'edit','recollect','propose'}:groups[a['role'],a['family_id'],a['world'],a['actor']].append((a.get('slot'),a.get('value')))
        by_role=defaultdict(list)
        for (role,*_),seq in groups.items():by_role[role].extend(a==b for a,b in zip(seq,seq[1:]))
        for role,values in by_role.items():legacy.append({'condition':condition,'role':role,'repeats':sum(values),'comparisons':len(values),'rate':statistics.mean(values),'source_sha256':sha256(run/f'{condition}_characters.jsonl')})
    write(REPORTS/'REPETITION_RECHECK.json',legacy)

    # Every printed numeric result below comes from generated tables.
    names=('C2','C3','C4','C5','C6','A1','A2','A3')
    lines=['# Exploration results — exploratory analysis under the frozen protocol','',
      f"Evidence cutoff: {audit['cutoff_utc']}. Primary: Qwen base defender, generator seed17, eight paired pilot families, 16-turn episodes, 12 opportunities. No new model calls.",'',
      '| Condition | Mean episode categories | Pooled categories | Mean two-action sequences | Mean transition types | Structurally substantive /192 | Character input+output tokens |',
      '|---|---:|---:|---:|---:|---:|---:|']
    for c in names:
        r=primary[c];token='N/A: deterministic' if not r['input_tokens'] else str(int(r['input_tokens'])+int(r['output_tokens']))
        lines.append(f"| {c} | {float(r['mean_episode_coverage']):.4f} | {r['pooled_coverage']} | {float(r['mean_sequence_coverage']):.4f} | {float(r['mean_transition_coverage']):.4f} | {r['substantive']} | {token} |")
    lines.extend(['',f"Primary C5−C3: **{contrast['difference']:+.4f} categories per episode**, paired-family 95% interval **[{contrast['family_interval'][0]:+.4f}, {contrast['family_interval'][1]:+.4f}]**. Ten thousand family resamples preserve both worlds. One generator seed and eight families do not establish equivalence or population generality.",
      '', 'Zero transition coverage for C2 means unavailable pre-action character observations, not zero physical transitions. Missing-state actions are excluded from that particular category count. A3 loses coverage through rejected actions in reserved communication slots; this is a design/formatting difference, not an isolated semantic effect of relationships.',
      '', '## Persistence and complementarity','',
      '| Condition/role | Same slot/value / comparisons | Rate |','|---|---:|---:|'])
    for r in legacy:lines.append(f"| {r['condition']} {r['role']} | {r['repeats']}/{r['comparisons']} | {r['rate']:.2%} |")
    lines.extend(['','| Observable | C3 | C5 |','|---|---:|---:|'])
    for label,field in [('Collective categories beyond the largest actor, mean/episode','mean_collective_beyond_largest_actor'),
                        ('API/reference changes during repeated goals','same_goal_tactic_changes'),
                        ('Repeated-goal comparisons, denominator','same_goal'),
                        ('Returns after a different direct goal','returns_after_other_goal'),
                        ('Structurally substantive applied actions /192 opportunities','substantive_applied'),
                        ('Recorded working-memory changes, including notes /192','memory_changes'),
                        ('Immediate targeted-state correct-to-incorrect transitions /192','correct_to_incorrect_edits'),
                        ('Immediate targeted-state incorrect-to-correct transitions /192','incorrect_to_correct_edits')]:
        lines.append(f"| {label} | {primary['C3'][field]} | {primary['C5'][field]} |")
    lines.extend(['','These are descriptive counts with dependent actions. Changes in API/reference class are tactic proxies, not semantic development. Targeted-state transitions compare the same-turn pre/post working state; they do not measure the causal effect on the following answer. Notes, peer delivery and executable decisions are different channels. Full action frequencies, validity reasons, source-visible contradictions and adoption flags retain their denominators in the CSV tables.'])
    categories=read(REPORTS/'primary_category_overlap.json')
    lines.extend(['',f"Pooled overlap: {len(categories['shared'])} shared categories, {len(categories['C5_only'])} C5-only and {len(categories['C3_only'])} C3-only. The full union spends twice the intervention budget and is not an improvement estimate.",'',
      '| Equal-budget archive | Mean categories | Qualification |','|---|---:|---|',
      f"| C3,12 opportunities per episode | {float(primary['C3']['mean_episode_coverage']):.4f} | Single trajectory |",
      f"| C5,12 opportunities per episode | {float(primary['C5']['mean_episode_coverage']):.4f} | Single trajectory |",
      f"| Six C3 + six C5 prefix opportunities | {statistics.mean(float(r['mixture_half_prefix']) for r in overlap):.4f} | Two initial trajectories; actual costs reported separately |",
      '', 'At the whole-archive level, balanced methods across paired families can add categories at the same number of opportunities. This is a different question from within-episode breadth.'])
    for r in whole:lines.append(f"- {r['condition']}: {r['mean']:.2f} categories (range {r['minimum']}–{r['maximum']} across100fixed family orderings;192opportunities).")
    lines.extend(['','All whole-archive allocations use 192 character calls and 256 defender calls. Actual prompt/history and output tokens differ:','',
      '| Archive | Mean character tokens | Mean defender tokens | Total-token allocation range |','|---|---:|---:|---:|'])
    for method in ('C3','C5','balanced_mixture'):
        values=[r for r in archive_costs if r['method']==method]
        lines.append(f"| {method} | {statistics.mean(r['character_tokens'] for r in values):.2f} | {statistics.mean(r['defender_tokens'] for r in values):.2f} | {min(r['total_tokens'] for r in values)}–{max(r['total_tokens'] for r in values)} |")
    lines.append('\nThese are measured token sums from archived trajectories, not condition-specific timing or equal FLOPs. The primary chronological token-prefix contrasts are in `primary_paired_contrasts.json`.')
    lines.extend(['','## Main collections remain observational','',
      '| Contrast | Seed | Round | Shared defender weights | Mean coverage difference | Family95% interval |',
      '|---|---:|---:|---|---:|---|'])
    for r in read(REPORTS/'main_collection_contrasts.json'):
        lines.append(f"| C5−{r['second']} | {r['seed']} | {r['round']} | {r['same_defender_weights']} | {r['difference']:+.3f} | [{r['family_interval'][0]:+.3f}, {r['family_interval'][1]:+.3f}] |")
    lines.extend(['','These estimates are conditional on the named generator seed. Round1 uses different trained defenders and families. No seed population interval or causal learning effect is inferred. Main C2/C6/A2/A3 and C5seed43 were absent at the cutoff. Later completions do not enter these tables.',
      '', '## Scientific assessment','',
      '**Inconclusive for broader useful exploration.** The primary endpoint and measured-token checks do not show a clear C5 breadth advantage. Higher typed-goal repetition supports persistent pursuit in this narrow sense, while API/reference changes require semantic validation before they count as tactic development. Some pooled categories are complementary, and balanced archives can gain modest coverage, but the within-episode mixture does not improve mean coverage.',
      '', 'The similar motive-only results do not identify a biography contribution. History/peer pilot differences remain entangled with action validity, routing, sampling variation and descriptor mechanics. Distinct owned slots permit simultaneous adoption. Source visibility can change a descriptor even when the claim is repeated verbatim. Nothing here shows the trained defender becoming a better explorer.',
      '', 'Retain original antagonist-free outcomes: C5−C3 is negative at both currently matched completed seeds. Exploration generation is a separate endpoint; it does not reverse those findings. Human semantic labels are pending.'])
    (REPORTS/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    manuscript=[ '# Exploratory manuscript section — author review required','',
      'After observing mixed/negative defender-transfer results, we conducted a separate frozen-snapshot audit of generator exploration. The primary comparison used the same untrained Qwen defender and eight paired pilot families. We counted canonicalized action/route/value/reference descriptors at twelve opportunities, retaining failed, contradictory and rejected attempts in the budget. Descriptor categories are observable proxies; semantic coherence and tactic novelty require independent review.','',
      f"C5 reached {float(primary['C5']['mean_episode_coverage']):.2f} categories per episode versus {float(primary['C3']['mean_episode_coverage']):.2f} for C3 (difference {contrast['difference']:+.2f}; paired-family95% interval [{contrast['family_interval'][0]:+.2f}, {contrast['family_interval'][1]:+.2f}]). Pooled coverage was {primary['C5']['pooled_coverage']} versus {primary['C3']['pooled_coverage']}. These one-seed pilot estimates neither demonstrate a breadth advantage nor establish equivalence.",'',
      f"There were {len(categories['C5_only'])} C5-only and {len(categories['C3_only'])} C3-only categories. A six-plus-six prefix archive averaged {statistics.mean(float(r['mixture_half_prefix']) for r in overlap):.2f} categories, below either twelve-opportunity single-method mean. Conversely, equal-opportunity whole-episode mixtures averaged {whole[-1]['mean']:.2f} pooled categories across100predefined family orderings, with range {whole[-1]['minimum']}–{whole[-1]['maximum']}. This limited archive complementarity is not a demonstrated semantic or learning benefit.",'',
      'Characters repeated typed goals more frequently than the generic comparator. Some API/reference changes occurred during repeated goals, but an illustrative repeated claim acquired different descriptors solely because its reference became unavailable. Another peer message supplied a substantive correction with an unspecified typed value. These observations show both overcounting and underdescription risks of automatic proxies; they are AI-assisted readings, not human validation.','',
      'The main-collection results were analyzed separately by seed and round. Round-zero weights were shared; refreshed defenders were condition-specific. No causal relationship between category coverage and final accuracy is identified. The evidence presently supports an informative limit and a modest complementarity hypothesis, not an established character-specific exploration advantage. The decisive next control is coherent-diversity-instructed generic generation under the same fixed defender and total budget. Biographies, histories, interaction and mutually incompatible utilities require their corresponding controls.']
    (HERE/'MANUSCRIPT_SECTION.md').write_text('\n'.join(manuscript)+'\n')
    claims=[
      ('Broader observable coverage','Not established','Primary paired contrast and cost prefixes','Small one-seed pilot; main differences near zero'),
      ('Persistent typed goals','Observed in this pilot','REPETITION_RECHECK.json','Repetition can be fixation; not semantic development'),
      ('Different tactics during same goal','Proxy variation observed; semantic status pending','persistence_by_role.csv and human packet','API/reference changes can overcount tactic changes'),
      ('Complementary categories','Descriptive archive evidence','primary_category_overlap.json; whole_archive_summary.json','Within-episode equal-budget mixture does not improve; category semantics unvalidated'),
      ('Narrative biography benefit','Not established','C5/A1 pilot and matched main-collection tables','No clear unique biography contribution; no equivalence claim'),
      ('History or peer mechanism','Unresolved','A2/A3 pilot context; action_validity.csv','Private history, routing and rejected actions complicate attribution'),
      ('Mutually incompatible goals','Not implemented by distinct owned slots','GOAL_COMPATIBILITY.json','Some utility terms involve peers; no optimized game or rivalry inferred'),
      ('Defender learns to explore','Not measured','No exploration-choice evaluation in these traces','Requires proposed interactive diagnosis task'),
      ('Exploration causes better task learning','Not established','Original negative/mixed main results retained','Severity, exposure and defender state confound associations')]
    write_csv(REPORTS/'claim_to_evidence.csv',[dict(zip(('claim','status','evidence','limit'),r)) for r in claims])
    (HERE/'CLAIM_TO_EVIDENCE.md').write_text('# Claim-to-evidence table\n\n| Claim | Status | Evidence | Limit |\n|---|---|---|---|\n'+'\n'.join('| '+' | '.join(r)+' |' for r in claims)+'\n')
    write(REPORTS/'REPORT_PROVENANCE.json',{'script_sha256':sha256(Path(__file__)),'scientific_manifest_sha256':sha256(HERE/'SCIENTIFIC_MANIFEST.json'),
      'inputs':{n:sha256(REPORTS/n) for n in ['coverage_curves.csv','primary_paired_contrasts.json','primary_overlap.csv','archive_rarefaction.csv','main_collection_contrasts.json']},
      'outputs':{str(p.relative_to(HERE)):sha256(p) for p in [REPORTS/'RESULTS.md',HERE/'MANUSCRIPT_SECTION.md',HERE/'CLAIM_TO_EVIDENCE.md',REPORTS/'cost_accounting.csv',REPORTS/'run_cost_reconciliation.csv']}})
    print({'cost_cells':len(costs),'reconciled_runs':len(reconciliation),'report':str((REPORTS/'RESULTS.md').relative_to(ROOT))})

if __name__=='__main__':main()
