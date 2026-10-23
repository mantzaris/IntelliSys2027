"""Design sensitivity, never an assumed result or test-significance stopping rule."""
from pathlib import Path
import json
import numpy as np


def simulate(n_families: int, baseline: float, discordance: float, seed_sd: float,
             effect: float=.05, n_seeds: int=3, trials: int=2000, seed: int=1208) -> dict:
    """Paired-outcome simulation with common family shocks and seed shifts.

    70% of a seed's family cells share a common latent uniform draw, inducing
    family dependence across training seeds. This is an explicit sensitivity
    assumption, not an estimated correlation from the tiny engineering pilot.
    Analytic two-way variance approximation is used for design screening only;
    the planned results use the paired bootstrap implemented in analysis.py.
    """
    rng=np.random.default_rng(seed);covered=0;detected=0;widths=[]
    if discordance<abs(effect):raise ValueError("Impossible paired discordance")
    for _ in range(trials):
        shared=rng.random((1,n_families));individual=rng.random((n_seeds,n_families))
        uniforms=np.where(rng.random((n_seeds,n_families))<.7,shared,individual)
        shifts=rng.normal(0,seed_sd,n_seeds)
        delta=np.clip(effect+shifts,-discordance,discordance)[:,None]
        positive=(discordance+delta)/2;negative=(discordance-delta)/2
        differences=(uniforms<positive).astype(float)-(uniforms>=1-negative).astype(float)
        estimate=differences.mean()
        family_means=differences.mean(axis=0);seed_means=differences.mean(axis=1)
        variance=family_means.var(ddof=1)/n_families+seed_means.var(ddof=1)/n_seeds
        half=1.96*np.sqrt(max(variance,1e-12))
        detected+=estimate-half>0;covered+=estimate-half<=effect<=estimate+half;widths.append(2*half)
    return {"families":n_families,"seeds":n_seeds,"baseline_reference":baseline,
            "effect":effect,"discordance":discordance,"seed_sd":seed_sd,"trials":trials,
            "detection_fraction":detected/trials,"interval_coverage":covered/trials,
            "mean_interval_width":float(np.mean(widths)),"family_sharing_probability":.7,
            "qualification":"Illustrative paired design sensitivity, not a guaranteed power calculation; baseline is contextual because discordance determines difference variance."}


def main():
    root=Path.cwd();output=root/"reports/tables/power_sensitivity.json"
    output.parent.mkdir(parents=True,exist_ok=True)
    rows=[simulate(n,.25,d,s) for n in (120,160,240) for d in (.1,.25,.4) for s in (0.,.02,.05)]
    output.write_text(json.dumps(rows,indent=2)+"\n")
    print(json.dumps({"simulations":len(rows),"path":str(output)}))


if __name__=="__main__":main()
