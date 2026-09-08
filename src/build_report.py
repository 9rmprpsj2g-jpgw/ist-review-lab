"""Build the shareable PDF from measured result files. Optional: reportlab."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from .data import ROOT
from .durable_io import atomic_file


def main():
    pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    pdfmetrics.registerFontFamily('DejaVu', normal='DejaVu', bold='DejaVu-Bold', italic='DejaVu', boldItalic='DejaVu-Bold')
    out=ROOT/'output/pdf';out.mkdir(parents=True,exist_ok=True)
    summary=pd.read_csv(ROOT/'results/summary.csv',index_col=0)
    topics=pd.read_csv(ROOT/'results/by_topic.csv',index_col=0)
    verify=json.loads((ROOT/'results/verification.json').read_text())
    navy=colors.HexColor('#142E3B');teal=colors.HexColor('#087F8C');grey=colors.HexColor('#536777')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleCustom',fontName='DejaVu-Bold',fontSize=32,leading=35,textColor=navy,spaceAfter=16))
    styles.add(ParagraphStyle(name='Deck',fontName='DejaVu',fontSize=14,leading=20,textColor=grey,spaceAfter=16))
    styles.add(ParagraphStyle(name='SectionCustom',fontName='DejaVu-Bold',fontSize=19,leading=23,textColor=navy,spaceAfter=14))
    styles.add(ParagraphStyle(name='BodyCustom',fontName='DejaVu',fontSize=10,leading=14.5,textColor=navy,spaceAfter=11))
    styles.add(ParagraphStyle(name='SmallCustom',fontName='DejaVu',fontSize=8.2,leading=11.5,textColor=grey,spaceAfter=9))
    styles.add(ParagraphStyle(name='Kicker',fontName='DejaVu-Bold',fontSize=9,leading=12,textColor=teal,spaceAfter=13))
    styles.add(ParagraphStyle(name='Cell',fontName='DejaVu',fontSize=8.6,leading=11.5,textColor=navy))
    story=[]
    def p(s,style='BodyCustom'):return Paragraph(s,styles[style])
    def add(s,style='BodyCustom'):story.append(p(s,style))
    def table(headers,rows,widths):
        data=[[p(escape(str(x)),'Cell') for x in headers]]+[[p(escape(str(x)),'Cell') for x in row] for row in rows]
        t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDECEF')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),
            ('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),.7,teal),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F6F8')])]))
        story.append(t);story.append(Spacer(1,13))
    def chart(name,height):story.append(Image(str(ROOT/'results/figures'/name),width=490,height=height));story.append(Spacer(1,7))
    def newpage(kicker,title):
        story.append(PageBreak());add(kicker,'Kicker');add(title,'SectionCustom')

    add('RESEARCH REPRODUCTION / EDISCOVERY / SEPTEMBER 2026','Kicker')
    add('IST Review Lab','TitleCustom')
    add('Learn from review decisions.<br/>Find useful material sooner.','Deck')
    add('An AI-assisted portfolio foundation for Arhan Shah: a measured continuous active learning experiment and a separate prototype for prioritizing matter signals.','BodyCustom')
    table(['DOCUMENTS','EXPERIMENTS','PRIMARY RESULT'],[['23,149','105 runs','66.4% mean recall'],['Public RCV1 subset','5 topics x 3 starts x 7 methods','After 1,000 reviews']],[145,155,190])
    add('The experiment asks a practical question: if a reviewer keeps marking examples useful or not useful, does retraining help them find relevant material earlier? In the measured benchmark, the answer is yes.','BodyCustom')
    chart('recall_comparison.png',220.5)
    add('Primary metric: equal-weight mean topic recall across five topics and three seeds. 1,000 reviews = 4.32% of the collection. Every method starts with the same known-positive seed in each paired run.','SmallCustom')
    add('<b>Scope:</b> This reproduces the core Auto TAR method on a smaller benchmark. It does not replicate the full paper or validate IST prospecting performance. The fictional BDR examples are a functional demonstration.','SmallCustom')

    newpage('01 / UNDERSTAND THE METHOD','A review loop you can explain')
    add('The research anchor is Cormack and Grossman\'s <i>Autonomy and Reliability of Continuous Active Learning for Technology-Assisted Review</i> (2015). <link href="https://arxiv.org/abs/1504.06868" color="#087F8C">Read the paper</link>.','BodyCustom')
    steps=[('1. Start','Begin with one confirmed relevant example.'),('2. Rank','Train a linear text classifier and score unread documents.'),('3. Review','Read the highest-ranked batch and give real relevance judgments.'),('4. Learn','Retrain using the accumulated judgments; then rank again.'),('5. Measure','Count the relevant documents found for the review effort spent.')]
    table(['STEP','WHAT HAPPENS'],steps,[85,405])
    add('Words become weighted numerical features. The SVM learns which features distinguish reviewed relevant examples from reviewed non-relevant ones. Its score orders documents; it is not a probability. Temporary assumed negatives help initialize the benchmark classifier and are discarded after each fit.','BodyCustom')
    add('<b>A calculation:</b> if you review 200 documents and find 75 of the collection\'s 100 relevant documents, precision is 75 / 200 = 37.5%, recall is 75 / 100 = 75%, and effort to 75% recall is 200 documents.','BodyCustom')
    add('Why use controls?','SectionCustom')
    table(['CONTROL','WHAT IT TESTS'],[
        ('Random review','What happens without useful ranking?'),
        ('Seed similarity','How far can resemblance to the first positive take us?'),
        ('Frozen SVM','Does ongoing feedback help beyond one initial fit?'),
        ('Uncertainty sampling','Does asking about ambiguous items outperform seeking likely positives?')],[125,365])
    add('The code keeps the learner separate from the evaluator. The learner sees words and revealed judgments. Only the evaluator knows all topic labels, enabling an offline reviewer simulation and exact recall calculations.','SmallCustom')

    newpage('02 / RESULTS AND THEIR LIMITS','The average does not tell the whole story')
    chart('gain_curves.png',215.6)
    names={'C12':'Legal / judicial','C15':'Corporate performance','C16':'Insolvency / liquidity','C18':'Ownership changes','GCRIM':'Crime / law enforcement'}
    rows=[]
    for code,name in names.items():
        r=topics.loc[code]
        rows.append([name,str(int(r.positives)),f'{r.mean_recall:.1%}',f'{r.recall_ceiling_at_1000:.1%}'])
    table(['TOPIC','RELEVANT','RECALL @ 1,000','POSSIBLE MAX'],rows,[185,80,115,110])
    add('<b>Interpret the ceiling:</b> corporate performance has 4,179 positives. A perfect ranking can recover at most 1,000 / 4,179 = 23.9% after 1,000 reviews. The model\'s 23.7% is near that maximum, not a poor ranking.','BodyCustom')
    add('For legal/judicial material, mean recall was 89.2%, ranging from 88.2% to 90.0% across three starts. The insolvency task has only 49 positives; a few documents can substantially change its recall. These ranges describe starting-seed sensitivity, not confidence intervals.','BodyCustom')
    add('730 rows repeat another token bag (3.15% of the pool). They were retained, and repeated reporting may make retrieval easier. Results on old news topics do not establish performance on new legal matters.','SmallCustom')

    newpage('03 / CHALLENGE AND VERIFY','Two attempted improvements; no hidden losses')
    a=summary.loc['auto_tar'];f=summary.loc['fixed_20'];e=summary.loc['explore_10']
    table(['EXPERIMENT','CHANGE IN RECALL @ 1,000','FITS / RUN'],[
        ('Auto TAR reference','Baseline','47'),
        ('Fixed 20-item batches',f'{(f.recall_at_1000-a.recall_at_1000)*100:+.2f} percentage points','250'),
        ('10% random exploration',f'{(e.recall_at_1000-a.recall_at_1000)*100:+.2f} percentage points','47')],[215,175,100])
    add(f'Fixed batches required {f.seconds/a.seconds:.1f} times the mean run time ({f.seconds:.2f}s versus {a.seconds:.2f}s). At 5,000 reviews, they gained only {(f.recall_at_5000-a.recall_at_5000)*100:.2f} percentage points of recall. More frequent retraining was not a clear improvement on the primary endpoint.','BodyCustom')
    add('Random exploration reduced average recall. It reached 90% recall within the 5,000-review budget in 14 of 15 runs; the reference reached it in all 15. All outcomes, including adverse results, remain in the package.','BodyCustom')
    add('Verification completed','SectionCustom')
    table(['CHECK','EVIDENCE'],[
        ('105 of 105 planned runs','Every topic, seed and method accounted for'),
        (f'{verify["metric_comparisons"]:,} metric comparisons','Independent arithmetic from saved review orders'),
        ('Six integrity tests','Temporary labels, repeat review, deterministic behavior, metrics and CSV handling'),
        ('5,000-position replay','One complete Auto TAR run reproduced its exact saved sequence'),
        ('Pinned source and settings','SHA-256 data checksum, configuration hash and package versions recorded')],[190,300])
    add('The original run took 6.7 minutes using two CPU workers. Recall targets never controlled selection or stopping. Missing recall-threshold effort stays censored; it is not zero. The package records within-batch and whole-batch effort separately.','SmallCustom')
    add('The simulation assumes a free-to-find known-positive seed and error-free topic labels. It is a fixed-pool retrieval experiment, not a conventional train/test assessment of future documents. No client data or IST outcome labels were used.','SmallCustom')

    newpage('04 / PAPER COMPARISON','A faithful loop with explicit scope changes')
    table(['COMPONENT','THIS PROJECT'],[
        ('Preserved','Relevance feedback, repeated SVM fitting, temporary negatives and growing batches'),
        ('Changed classifier','LinearSVC replaces SVMlight; solver and intercept treatment differ'),
        ('Changed data scope','23,149 rows and five topics, rather than the complete study'),
        ('Changed feature statistics','Cornell ltc weights and vocabulary are calculated on this subset'),
        ('Changed sampling','Temporary negatives are sampled only from unread documents'),
        ('Changed controls','Local controls are not exact implementations of the paper\'s SAL/SPL baselines')],[155,335])
    add('Published numerical reference','SectionCustom')
    table(['TREC TOPIC','PAPER CAL','PAPER AUTO TAR*'],[['201','3,400','2,400'],['202','9,100','8,000'],['203','4,800','4,300'],['207','9,400','8,000']],[155,155,180])
    add('*Documents reviewed to achieve 75% recall; random-seed variant, Table II. These are the paper\'s values, not our results. They come from different legal tasks and cannot be numerically compared with our RCV1 subset to claim a replication error or superiority.','SmallCustom')
    add('<b>Research conclusion:</b> the smaller experiment supports the usefulness of feedback-driven ranking under its tested conditions. It does not establish exact reproduction of the paper\'s tables or broad reliability across legal matters.','BodyCustom')
    add('Primary sources','SectionCustom')
    add('<link href="https://arxiv.org/abs/1504.06868" color="#087F8C">Cormack and Grossman (2015): Auto TAR</link><br/><link href="https://jmlr.org/papers/v5/lewis04a.html" color="#087F8C">Lewis et al. (2004): RCV1 benchmark</link><br/><link href="https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multilabel.html" color="#087F8C">LIBSVM: public RCV1 representation</link>','SmallCustom')

    newpage('05 / USE AND DEVELOP THE PROJECT','Turn the research into your own portfolio work')
    add('For your IST role, use the measured experiment to understand and explain document prioritization. Use the separate BDR utility to test whether your own relevance judgments can improve the order in which you research matter signals.','BodyCustom')
    table(['DAILY STEP','YOUR ACTION'],[
        ('Capture evidence','Add account, signal text, event date and source URL to the CSV template.'),
        ('Give judgments','Mark useful = 1, reviewed but not useful = 0; leave unread rows blank.'),
        ('Review the queue','Inspect the top 20, including source, age and model word cues.'),
        ('Retrain','Update labels in the original CSV and rerun the command.'),
        ('Validate','Compare with your current process on later dates and different accounts.')],[115,375])
    add('The practical queue uses a class-balanced SVM trained on confirmed labels. This differs from the benchmark: temporary negatives behaved poorly in the tiny fictional demo. That adjustment solves a functional bootstrap issue; it does not establish sales effectiveness.','BodyCustom')
    add('What to open first','SectionCustom')
    table(['DELIVERABLE','PURPOSE'],[
        ('Walkthrough.ipynb','Executed learning notebook; usable locally or in Colab'),
        ('docs/IMPLEMENTATION_TASKS.md','Eight implementation and learning tasks'),
        ('docs/IST_PLAYBOOK.md','Signal rubric, daily usage and real-data pilot design'),
        ('RESULTS.md and results/','All measurements, figures and review trails'),
        ('src/ and tests/','Runnable implementation and integrity checks')],[225,265])
    add('A strong next contribution is an independently judged pilot on 200-500 sourced signals, split by account/matter and time. Measure useful items per 20 reviews and research time. Treat meetings and opportunities as separate outcomes.','BodyCustom')
    add('The next step is to run your own extension and document its outcome. The shipped signals are fictional, and no external outreach is performed. This independent educational project is not endorsed by IST.','SmallCustom')

    def footer(canvas,doc):
        canvas.saveState();w,h=A4
        canvas.setStrokeColor(colors.HexColor('#DDE4E9'));canvas.line(50,43,w-50,43)
        canvas.setFillColor(grey);canvas.setFont('DejaVu',8)
        canvas.drawString(50,29,'IST REVIEW LAB  |  Scoped method reproduction  |  AI-assisted project')
        canvas.drawRightString(w-50,29,str(doc.page));canvas.restoreState()
    with atomic_file(out/'IST_Review_Lab_Report.pdf', 'wb') as stream:
        pdf=SimpleDocTemplate(stream,pagesize=A4,rightMargin=50,leftMargin=50,
            topMargin=43,bottomMargin=57,title='IST Review Lab - Research Reproduction',author='Prepared for Arhan Shah with AI assistance')
        pdf.build(story,onFirstPage=footer,onLaterPages=footer)
    print(out/'IST_Review_Lab_Report.pdf')


if __name__=='__main__':main()
