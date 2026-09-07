"""Generate tables and publication-style figures directly from audited runs."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .data import ROOT

NAMES={'random':'Random review','seed_similarity':'Seed similarity','frozen_svm':'Frozen SVM',
       'uncertainty':'Uncertainty sampling','auto_tar':'Auto TAR','fixed_20':'Fixed batches of 20',
       'explore_10':'10% random exploration'}
TOPICS={'C12':'Legal / judicial','C15':'Corporate performance','C16':'Insolvency / liquidity',
        'C18':'Ownership changes','GCRIM':'Crime / law enforcement'}


def table_md(frame):
    rows=[list(frame.columns)]+frame.astype(str).values.tolist()
    return '\n'.join(['| '+' | '.join(rows[0])+' |','|'+'|'.join(['---']*len(rows[0]))+'|']+
                     ['| '+' | '.join(r)+' |' for r in rows[1:]])


def main():
    f=pd.read_csv(ROOT/'results/runs.csv')
    order=list(NAMES)
    metrics=['recall_at_1000','recall_at_5000','precision_at_20','seconds','fits']
    summary=f.groupby(['topic','policy'])[metrics].mean().groupby('policy').mean().reindex(order)
    summary['runs']=f.groupby('policy').size()
    summary['reached_75']=f.groupby('policy').effort_at_75.count()
    summary['reached_90']=f.groupby('policy').effort_at_90.count()
    summary.to_csv(ROOT/'results/summary.csv')
    topic=f[f.policy=='auto_tar'].groupby('topic').agg(
        positives=('positives','first'),mean_recall=('recall_at_1000','mean'),
        min_recall=('recall_at_1000','min'),max_recall=('recall_at_1000','max'),
        mean_effort_75=('effort_at_75','mean'),mean_effort_90=('effort_at_90','mean'))
    topic['recall_ceiling_at_1000']=np.minimum(1,1000/topic.positives)
    topic.to_csv(ROOT/'results/by_topic.csv')
    base=f[f.policy=='auto_tar'].set_index(['topic','seed'])
    paired=[]
    for policy in ['fixed_20','explore_10']:
        variant=f[f.policy==policy].set_index(['topic','seed'])
        for idx in base.index:
            delta=float(variant.loc[idx,'recall_at_1000']-base.loc[idx,'recall_at_1000'])
            paired.append({'topic':idx[0],'seed':idx[1],'policy':policy,'delta_recall_at_1000':delta})
    pd.DataFrame(paired).to_csv(ROOT/'results/paired_differences.csv',index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white'})
    colors={'random':'#97A5B0','seed_similarity':'#BAC4CB','frozen_svm':'#526C86',
            'uncertainty':'#987AAA','auto_tar':'#087F8C','fixed_20':'#DC923C','explore_10':'#BB5D66'}
    out=ROOT/'results/figures';out.mkdir(exist_ok=True)
    fig,ax=plt.subplots(figsize=(10,4.5),layout='constrained')
    values=summary.recall_at_1000*100
    ax.barh([NAMES[p] for p in order],values,color=[colors[p] for p in order],height=.62)
    ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('Mean topic recall after 1,000 reviews (%)')
    for i,value in enumerate(values):ax.text(value+1,i,f'{value:.1f}%',va='center',fontsize=10)
    ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    fig.savefig(out/'recall_comparison.png',dpi=180);fig.savefig(out/'recall_comparison.svg');plt.close(fig)
    curves={p:[] for p in order}
    for row in f.itertuples():
        audit=json.loads((ROOT/f'results/audits/{row.topic}_{row.seed}_{row.policy}.json').read_text())
        curves[row.policy].append(np.cumsum(audit['observed_labels'])/row.positives)
    curve_table=pd.DataFrame({'reviews':np.arange(1,5001)})
    for policy in order:curve_table[policy]=np.mean(curves[policy],axis=0)
    curve_table.to_csv(ROOT/'results/gain_curves.csv',index=False)
    fig,ax=plt.subplots(figsize=(10,4.4),layout='constrained')
    for policy in ['auto_tar','frozen_svm','uncertainty','random']:
        ax.plot(curve_table.reviews,curve_table[policy]*100,label=NAMES[policy],color=colors[policy],lw=2.4)
    ax.set(xlabel='Documents reviewed, including the seed',ylabel='Mean topic recall (%)',xlim=(0,5000),ylim=(0,100))
    ax.axvline(1000,color='#CBD2D8',ls=':',lw=1);ax.grid(alpha=.15);ax.legend(frameon=False,loc='lower right')
    fig.savefig(out/'gain_curves.png',dpi=180);fig.savefig(out/'gain_curves.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4),layout='constrained')
    torder=list(TOPICS)
    t=topic.loc[torder]
    ax.barh([TOPICS[p] for p in torder],t.recall_ceiling_at_1000*100,color='#E6ECF0',label='Maximum possible at this budget')
    ax.barh([TOPICS[p] for p in torder],t.mean_recall*100,color='#087F8C',height=.58,label='Auto TAR mean')
    ax.errorbar(t.mean_recall*100,np.arange(5),xerr=np.vstack([(t.mean_recall-t.min_recall)*100,(t.max_recall-t.mean_recall)*100]),fmt='none',ecolor='#183745',capsize=3)
    ax.invert_yaxis();ax.set(xlim=(0,110),xlabel='Recall after 1,000 reviews (%)')
    for i,v in enumerate(t.mean_recall*100):ax.text(v+2,i,f'{v:.1f}%',va='center')
    ax.legend(frameon=False,loc='lower right',fontsize=8);ax.grid(axis='x',alpha=.12)
    fig.savefig(out/'topic_recall.png',dpi=180);fig.savefig(out/'topic_recall.svg');plt.close(fig)
    display=pd.DataFrame({'Method':[NAMES[p] for p in order],
                          'Recall at 1,000':[f'{v:.1%}' for v in summary.recall_at_1000],
                          'Recall at 5,000':[f'{v:.1%}' for v in summary.recall_at_5000],
                          '90% reached by 5,000':[f'{int(v)}/15' for v in summary.reached_90]})
    topicdisplay=pd.DataFrame({'Topic':[TOPICS[p] for p in torder],
        'Relevant docs':[str(int(topic.loc[p,'positives'])) for p in torder],
        'Recall at 1,000':[f'{topic.loc[p,"mean_recall"]:.1%}' for p in torder],
        'Possible maximum':[f'{topic.loc[p,"recall_ceiling_at_1000"]:.1%}' for p in torder]})
    auto=summary.loc['auto_tar'];fixed=summary.loc['fixed_20'];explore=summary.loc['explore_10']
    report=f'''# IST Review Lab: measured results

This is a scoped reproduction of the Auto TAR protocol on a public RCV1-v2 subset, with a separate experimental queue for IST matter-signal research. It is not an exact replication of the original paper's result tables.

## Main finding

Auto TAR found an average of {auto.recall_at_1000:.1%} of each topic's relevant documents in the first 1,000 reviews. Random review found {summary.loc['random','recall_at_1000']:.1%}; a frozen SVM found {summary.loc['frozen_svm','recall_at_1000']:.1%}. These are equally weighted topic means across five topics and three starting seeds. The budget was 1,000 / 23,149 = 4.32% of the collection. This finding concerns topic retrieval, not the probability of an IST sale.

{table_md(display)}

![Comparison](results/figures/recall_comparison.png)

## Why the topics need separate interpretation

{table_md(topicdisplay)}

The performance topic has 4,179 positives. Even a perfect ranking can find at most 1,000 / 4,179 = 23.9% after 1,000 reviews. Its 23.7% measured recall is close to that ceiling; the small percentage does not mean the model failed. The insolvency topic has only 49 positives, so moving a handful of documents can change recall sharply. No claim of broad reliability follows from three starts.

There are 22,419 unique token bags among 23,149 documents: 730 rows repeat another bag (3.15%). They remain in the fixed review pool, so repeated reporting may make retrieval easier. This is disclosed rather than silently treating the records as independent matters.

![Gain curves](results/figures/gain_curves.png)

## Experiments that challenged the baseline

Fixed batches of 20 changed primary recall by {(fixed.recall_at_1000-auto.recall_at_1000)*100:+.2f} percentage points. They required 250 fits per run versus 47 for the growing schedule. Mean measured run time was {fixed.seconds:.2f} seconds versus {auto.seconds:.2f} seconds ({fixed.seconds/auto.seconds:.1f} times as much). At 5,000 reviews they changed recall by {(fixed.recall_at_5000-auto.recall_at_5000)*100:+.2f} percentage points. That is a tradeoff, not a clear primary-metric improvement.

Random exploration changed primary recall by {(explore.recall_at_1000-auto.recall_at_1000)*100:+.2f} percentage points. One run did not reach 90% recall within the budget, while the reference reached it in all 15 starts. Broadening exploration did not improve this fixed benchmark. `results/paired_differences.csv` retains all wins, ties and losses.

## Verification

All 105 planned runs finished. `src/verify_results.py` independently recomputes precision, recall and recall-threshold effort from the full review-order audit files. It checks budget, unique IDs, source labels, shared seeds and censored thresholds. Six unit tests check label isolation, temporary negatives, repeat reviews, deterministic execution, metric arithmetic and the operational CSV queue. One complete Auto TAR run is replayed and compared with its saved order.

The seed is known positive and costs one review; finding it is free in this simulation. The 20-item precision metric therefore has a built-in advantage and is secondary. All learning curves use perfect benchmark labels, not actual reviewer errors. Recall-at-75 and recall-at-90 are evaluated after the run, never used to decide when to stop. Batch-complete effort is separately retained.

## What this supports for IST

You can demonstrate and explain reviewer feedback with actual measured results. You can also try the separate `bdr_queue` tool on dated, sourced matter signals you have labeled yourself. That utility uses confirmed positive and negative labels and must be evaluated on real future data before claiming prospecting gains. Its fictional demonstration is a functional check only.

Read `docs/IMPLEMENTATION_TASKS.md` for the learning path, `docs/PAPER_COMPARISON.md` for the research comparison, and `docs/IST_PLAYBOOK.md` for the daily workflow and pilot design. The downloadable package is an AI-assisted project foundation; make and defend your own changes before presenting it as independently authored work.
'''
    (ROOT/'RESULTS.md').write_text(report)
    print(display.to_string(index=False))


if __name__=='__main__':main()
