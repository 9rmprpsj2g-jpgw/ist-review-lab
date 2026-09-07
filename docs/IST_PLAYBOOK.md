# Use this as an IST BDR

The most direct eDiscovery use is explaining and demonstrating why reviewer feedback can reduce the amount of material a team must examine. The experimental BDR use is ranking a supplied collection of matter signals by which ones deserve your research time next. The benchmark does not establish that the model predicts who will buy.

## A concrete daily workflow

1. Put public matter updates or approved internal research notes into `data/my_signals.csv`, using `data/signals_template.csv` as the schema. Each row is one evidence item about an account and matter, not just a lawyer's biography.
2. Keep the event date, source URL and exact factual basis. A recently published article can describe an old event; use the event date when known. Missing dates stay unknown.
3. Start by reviewing a varied set of examples. Aim for roughly 10 useful and 10 non-useful examples as a practical starting point, not a proven sample-size requirement. The program requires at least one of each.
4. Use `label=1` for an event that merits further IST matter research now, `label=0` for an event you reviewed and found not useful, and a blank for an item you have not judged. Do not treat silence, uncertainty, or missing evidence as a confirmed negative.
5. Run the queue. Check the top 20 evidence items, their age, source and word cues. Investigate whether the account is involved, the matter is active, work is upcoming, and the service hypothesis makes sense.
6. Add judgments to the original input CSV and rerun. The new model learns from all confirmed labels. Put notes and the next action in your normal workflow after verification.

```bash
python -m src.bdr_queue --input data/my_signals.csv --output results/bdr_queue.csv --as-of 2026-09-07 --top 20
```

Use your actual review date. Rankings use text and reviewer judgments; dates are shown for inspection and are not included in the model. A score is an uncalibrated ranking margin, not confidence, likelihood of a meeting, or purchasing intent. Word cues are contributions to the classifier score, not proof of a real commercial need.

## What makes a useful signal?

| Evidence to check | Possible IST connection | What you must still establish |
|---|---|---|
| An active dispute describes missing emails, personal devices or data transfer | Digital forensics and collection | What evidence needs preservation or collection, who controls it, and whether help is needed |
| A production deadline and identifiable electronic records | Processing and hosting | Timing, data format, volume, existing platform and vendor arrangements |
| A large collection with a constrained review schedule | Managed review or overflow | Real review volume, staffing pressure and whether external support is possible |
| A deposition calendar in an active matter | Court reporting | Actual dates, jurisdiction, scheduling owner and existing arrangements |
| Bankruptcy, merger, leadership change or a new office alone | A research prompt | Evidence of an actual matter-related workload; the event alone is insufficient |

These are working hypotheses tied to the services in your request, not automatic routing decisions. The CSV retains `service_hypothesis` if you supply it; the model does not invent service needs or infer facts missing from the source.

## What the shipped demonstration proves

`example_signals.csv` contains 24 fictional evidence snippets, four pre-labeled and 20 unreviewed. Accounts begin with 'Example', source URLs are blank and the `source_type` column identifies the synthetic demonstration. It demonstrates CSV loading, ranking, explanations, dates and re-ranking. It has no measured sales performance. Do not import these rows as real CRM leads.

The demonstration deliberately contains a stale review story, an undated inquiry, a dismissed case and a trade-secret signal with different vocabulary. A word-based classifier can miss context, negation and unfamiliar language. Inspect these failures when deciding whether this tool helps you. Exact duplicates are excluded with an audit trail; near duplicates and multiple reports on the same matter still require grouping.

## A real pilot that would support a stronger claim

Collect 200-500 distinct public matter signals across multiple weeks as a planning target. Keep a written labeling rubric. Have an experienced AE independently review at least the evaluation pool or a substantial random sample, recording disagreements. Group repeated accounts and matters before splitting data. Develop the model using earlier dates; reserve later dates and different accounts for evaluation. Do not use outcomes from that reserve set to tune the model.

Compare the queue against your current research order and a documented keyword baseline. For a fixed daily budget, measure useful items found per 20 examined, minutes per verified opportunity and false positives. If you want recall, independently judge the whole bounded pool or use an appropriate sampling estimate with uncertainty. Log meetings and opportunities separately and wait for outcomes; a benchmark on topic labels cannot establish revenue lift.

Keep an audit of source, event date, reviewer, judgment, model version and reason for follow-up. No sending, CRM writing or automatic daily ingestion is included in this prototype.

## A natural sales conversation

You can explain that you built a small research reproduction to understand how document prioritization learns from reviewer feedback. Then ask how the prospect currently handles review when the amount of material rises or the production timetable tightens. Use the project to make a concrete technical idea understandable. Its experimental percentages are not claims about IST's platform, client matters or guaranteed savings.
