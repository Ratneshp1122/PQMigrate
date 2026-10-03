"""Run D18 baselines and ablations on the exact PQMigrateBench corpus."""
from __future__ import annotations
import argparse, ast, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from pqc_migration_tool.benchmarks.evaluate import DATASET_PATH, _metrics, load_cases
from pqc_migration_tool.resolver.context_inference import infer_rsa_usage

def _unknown(evidence="No operation predicted."):
    return {"is_operation":False,"role":"unknown","operation":"unknown","protocol_context":"unknown","confidence":"ambiguous","evidence":evidence}

def primitive_lookup(source):
    if "rsa" not in source.lower(): return _unknown("No RSA token.")
    return {"is_operation":True,"role":"unknown","operation":"unknown","protocol_context":"unknown","confidence":"ambiguous","evidence":"Lexical RSA token; no syntax, identity, role, or context proof."}

def ast_call_only(source):
    try: tree=ast.parse(source)
    except SyntaxError: return _unknown("AST parse failure.")
    observed=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute): continue
        method=node.func.attr
        if method in {"sign","verify"}: observed.append(("signature",method))
        elif method in {"encrypt","decrypt"}: observed.append(("encryption",method))
    roles={role for role,_ in observed}
    if len(roles)!=1 or not observed: return _unknown("No unique method-name role.")
    role,operation=observed[0]
    return {"is_operation":True,"role":role,"operation":operation,"protocol_context":"unknown","confidence":"inferred","evidence":"AST method name only; receiver identity is not resolved."}

def full_pipeline(source):
    result=infer_rsa_usage(source)
    return {"is_operation":result.role.value!="unknown","role":result.role.value,"operation":result.operation.value,"protocol_context":result.protocol_context.value,"confidence":result.confidence.value,"evidence":result.evidence}

def no_session_secret_flow(source):
    predicted=full_pipeline(source)
    if predicted["role"]=="key_transport":
        predicted=dict(predicted,role="encryption",evidence="Ablation: session-secret evidence removed; transport collapses to encryption.")
    return predicted

def no_protocol_context(source):
    return dict(full_pipeline(source),protocol_context="unknown")

SYSTEMS:dict[str,Callable[[str],dict]]={"primitive_lookup":primitive_lookup,"ast_call_only":ast_call_only,"no_session_secret_flow":no_session_secret_flow,"no_protocol_context":no_protocol_context,"full_pipeline":full_pipeline}

def _additional_metrics(rows):
    evaluated=[row for row in rows if row["accounting"]=="evaluated"]
    labelled=[row for row in evaluated if row["gold"]["protocol_context"]!="unknown"]
    context_correct=sum(row["predicted"]["protocol_context"]==row["gold"]["protocol_context"] for row in labelled)
    exact=sum(row["predicted"]["is_operation"]==row["gold"]["is_operation"] and (not row["gold"]["is_operation"] or (row["predicted"]["role"]==row["gold"]["role"] and row["predicted"]["operation"]==row["gold"]["operation"])) for row in evaluated)
    return {"exact_operation_role_accuracy":round(exact/len(evaluated),6) if evaluated else None,"labelled_protocol_cases":len(labelled),"protocol_context_accuracy":round(context_correct/len(labelled),6) if labelled else None}

def _delta(value,reference):
    return round(value-reference,6) if value is not None and reference is not None else None

def run(dataset=DATASET_PATH):
    path=Path(dataset).resolve(); cases=load_cases(path); systems={}
    for name,predictor in SYSTEMS.items():
        predictions=[]
        for case in cases:
            predicted=predictor(case["source"]); mismatches=[]
            if case["accounting"]=="evaluated":
                if predicted["is_operation"]!=case["gold"]["is_operation"]: mismatches.append("operation_presence")
                if case["gold"]["is_operation"] and predicted["role"]!=case["gold"]["role"]: mismatches.append("role")
                if case["gold"]["is_operation"] and predicted["operation"]!=case["gold"]["operation"]: mismatches.append("operation")
                if case["gold"]["protocol_context"]!="unknown" and predicted["protocol_context"]!=case["gold"]["protocol_context"]: mismatches.append("protocol_context")
            predictions.append({"id":case["id"],"split":case["split"],"category":case["category"],"accounting":case["accounting"],"gold":case["gold"],"predicted":predicted,"mismatches":mismatches})
        systems[name]={"metrics":_metrics(predictions),"additional_metrics":_additional_metrics(predictions),"error_count":sum(bool(row["mismatches"]) for row in predictions),"predictions":predictions}
    full=systems["full_pipeline"]["metrics"]; comparisons={}
    for name,result in systems.items():
        metrics=result["metrics"]
        comparisons[name]={"operation_f1_delta_vs_full":_delta(metrics["operation_detection"]["f1"],full["operation_detection"]["f1"]),"role_accuracy_delta_vs_full":_delta(metrics["role_resolution"]["end_to_end_role_accuracy"],full["role_resolution"]["end_to_end_role_accuracy"])}
    return {"schema_version":"2026.10.03-d18.1","generated_at":datetime.now(timezone.utc).isoformat(),"dataset":path.name,"dataset_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"case_count":len(cases),"label_status":"single_author_synthetic_pilot","claim_scope":"Same-corpus Python RSA ablation study; not product-wide accuracy.","systems":systems,"comparisons":comparisons}

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--dataset",default=str(DATASET_PATH)); parser.add_argument("--output"); args=parser.parse_args()
    report=run(args.dataset); payload=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if args.output: Path(args.output).write_text(payload,encoding="utf-8")
    for name,result in report["systems"].items():
        operation=result["metrics"]["operation_detection"]; role=result["metrics"]["role_resolution"]
        print(f"{name:24} f1={operation['f1']} role_e2e={role['end_to_end_role_accuracy']} errors={result['error_count']}")
    if not args.output: print(payload,end="")

if __name__=="__main__": main()
