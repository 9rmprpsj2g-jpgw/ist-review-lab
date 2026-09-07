"""Structural storage projection only: no data loading, model or experiment calls."""
import json
import math
from pathlib import Path


def estimate(policy, budget, n=23149):
    reviewed, batch, rounds, candidate_entries = 1, (20 if policy == 'fixed_20' else 1), 0, 0
    svm = policy not in ('random', 'seed_similarity')
    while reviewed < budget:
        rounds += 1
        if svm:
            candidate_entries += n-reviewed
        reviewed += min(batch, budget-reviewed)
        if policy != 'fixed_20':
            batch += math.ceil(batch/10)
    fits = (1 if policy == 'seed_only_frozen' else rounds) if svm else 0
    # Planning envelope, NOT measured audit file sizes: JSON row integer +
    # external ID string + full precision float, including list separators.
    # Assumes external IDs <= 12 ASCII characters. Metadata and selections
    # allowance includes retained legacy flat order/labels/batch boundaries.
    low = candidate_entries*24 + budget*80 + rounds*400 + fits*3000
    high = candidate_entries*48 + budget*160 + rounds*800 + fits*6000
    return dict(policy=policy,budget=budget,query_rounds=rounds,fits=fits,
                candidate_margin_entries=candidate_entries,
                estimated_bytes_low=low,estimated_bytes_high=high)


if __name__ == '__main__':
    policies = ['random','seed_similarity','seed_only_frozen','uncertainty','auto_tar','fixed_20','explore_10']
    result = {'kind':'structural estimate, not a measured run', 'collection_size':23149,
              'assumptions':'24–48 bytes per margin entry; 80–160 per reviewed document; 400–800 per round; 3000–6000 per fit. External IDs <=12 ASCII characters. Uncompressed JSON; Python RAM usage may be substantially larger.',
              'runs':[estimate(p,b) for p in policies for b in (5000,23149)]}
    Path(__file__).with_name('audit_size_estimates.json').write_text(json.dumps(result,indent=2)+'\n')
    for row in result['runs']:
        print(row['policy'],row['budget'],row['query_rounds'],row['candidate_margin_entries'],
              round(row['estimated_bytes_low']/1e6,2), round(row['estimated_bytes_high']/1e6,2))
