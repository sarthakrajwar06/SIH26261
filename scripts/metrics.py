"""Measured synthetic-fixture metrics, NOT real-world OCR/forgery performance."""
import sys,time,json,subprocess
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from generate_fixtures import generate
from app.document_ai.extract import extract,inspect_file
from app.rules.engine import evaluate
ROOT=Path(__file__).resolve().parents[1]

def main():
    labels=generate();correct=total=tp=fp=fn=atp=afp=afn=0;times=[];all_findings=[]
    for item in labels:
        data=(ROOT/'data/synthetic'/item['file']).read_bytes();start=time.perf_counter()
        mime,sha=inspect_file(data,20*1024*1024);result=extract(data,mime);times.append(time.perf_counter()-start)
        observed={f['field_name']:f['normalized_value'] for f in result['fields']}
        for k,v in item['fields'].items():total+=1;correct+=observed.get(k)==v
        doc=dict(id='fixture',checksum=sha,document_category='certificate',processing_status='COMPLETE',analysis=result)
        rules=[dict(id='expiry-v1',rule_id='expiry',evaluation_type='expiry',parameters={'field':'expiry_date'},title='DEMO expiry',severity='WARNING')]
        fields=[dict(f,document_id='fixture') for f in result['fields']]
        findings=evaluate({'id':'fixture-app','category_id':'demo'},{'identifier':'DEMO-MERIDIAN-001'},[doc],fields,rules,today=date(2026,10,25));all_findings.extend(findings)
        actual=item['scenario']=='expired_certificate';predicted=any(f['category']=='EXPIRY' and f['status']=='FAIL' for f in findings)
        tp+=actual and predicted;fp+=predicted and not actual;fn+=actual and not predicted
        actual_anomaly=item['scenario']=='metadata_anomaly';predicted_anomaly=any(f['category']=='METADATA' for f in findings)
        atp+=actual_anomaly and predicted_anomaly;afp+=predicted_anomaly and not actual_anomaly;afn+=actual_anomaly and not predicted_anomaly
    workflow=subprocess.run([sys.executable,'-m','pytest','backend/tests/test_workflow.py','-q'],cwd=ROOT,capture_output=True,text=True)
    out={'scope':'12 generated native-text synthetic PDFs only. Not scanned OCR, real-world fraud, or model accuracy.',
         'field_accuracy':correct/total,'fields_correct':correct,'fields_labeled':total,
         'expiry_validation_precision':tp/(tp+fp) if tp+fp else None,'expiry_validation_recall':tp/(tp+fn) if tp+fn else None,
         'metadata_indicator_precision':atp/(atp+afp) if atp+afp else None,'metadata_indicator_recall':atp/(atp+afn) if atp+afn else None,
         'mean_processing_seconds':sum(times)/len(times),'findings_with_evidence_percentage':100*sum(bool(f['evidence']) for f in all_findings)/len(all_findings),
         'end_to_end_test_double_workflow_completed':workflow.returncode==0,'live_supabase_workflow_tested':False}
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':main()
