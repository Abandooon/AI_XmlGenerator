#!/usr/bin/env python3
"""Cross-check manuscript data against retained records; standard library only.

No API, database, native validator or source generator is run. Counts and costs
are re-aggregated from original records and compared with retained review rows.
PIL decisions and paired statistics are replayed by the adjacent pure-function
inspector. Native validity itself is covered by verify_release.py. See the
machine report's evidence levels, especially retained Neo4j context counts.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import io
import json
from pathlib import Path
import re
import random
import math
import statistics
import sys
import tarfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
import check_pil_decision_flow as pil

GITHUB = "https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/"
MANUSCRIPT = "paper/current/english/main.tex"
AUTOZIP = "experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip"
VLLMTAR = "experiments/vllm/archives/atlas-vllm-uga-v6-3-4-paper-evidence-20260829.tar.gz"


def require(value, message):
    if not value: raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def one(items, description):
    values = list(items)
    require(len(values) == 1, description + ": expected one match, got " + str(len(values)))
    return values[0]


class Metrics:
    def __init__(self): self.values = {}

    def add(self, name, value, source, pointer, code, unit="count", denominator=None,
            level="RECOMPUTED_FROM_RECORDS"):
        require(name not in self.values, "Duplicate metric " + name)
        self.values[name] = dict(value=value, source=source, selector=pointer, code=code,
                                 unit=unit, denominator=denominator, evidence_level=level)

    def alias(self, name, value, parent, unit=None, denominator=None):
        p = self.values[parent]
        self.add(name, value, p["source"], p["selector"], p["code"], unit or p["unit"],
                 denominator, p["evidence_level"])


def autosar(root, metrics):
    genpath = "experiments/autosar/validation/generation_rows.json"
    reppath = "experiments/autosar/validation/repair_rows.json"
    code = "experiments/autosar/offline/verify.py"
    grows, rrows = read(root / genpath), read(root / reppath)
    with zipfile.ZipFile(root / AUTOZIP) as z:
        names = z.namelist()
        def member(suffix): return one((n for n in names if n.endswith(suffix)), suffix)
        def obj(suffix): return json.loads(z.read(member(suffix)))
        records = obj("formal_v20/generation/experiment_results.json")["records"]
        original = {r["run_id"]: r for r in records}
        require(set(original) == {r["run_id"] for r in grows}, "AUTOSAR generation membership differs")
        allcalls, xmis, evaluations = [], [], []
        for r in grows:
            src = original[r["run_id"]]
            require((r["decision"] == "PASS") == (src["independent_decision"] == "PASS"), "AUTOSAR generation outcome differs")
            suffix = f"generation/runs/gpt-5.6-luna/{r['case_id']}/R{r['repetition']}/repair-off/attempt-001/independent_evaluation.json"
            n = member(suffix); run = n.removesuffix("independent_evaluation.json")
            e = json.loads(z.read(n)); evaluations.append(e)
            require(len(e["structural_obligations"]) == r["structural_obligations"], "AUTOSAR obligation count differs")
            require(len(e["reference_integrity"]) == r["local_references"], "AUTOSAR reference count differs")
            allcalls.extend(json.loads(s) for s in z.read(run + "provider_calls.jsonl").splitlines() if s.strip())
            for f, expected in src["artifact_hashes"].items():
                if f.endswith(".arxml") and f.startswith("atlas_output/ARXML/"):
                    data = z.read(run + f)
                    require(sha(data) == expected, "AUTOSAR artifact bytes differ")
                    tree = ET.fromstring(data)
                    def depth(el): return 1 + max((depth(c) for c in el), default=0)
                    xmis.append(dict(case=r["case_id"], repeat=r["repetition"], component="/Components/" in f,
                                     elements=sum(1 for _ in tree.iter()), depth=depth(tree), member=run+f))
        require(sum(c["usage"]["total_tokens"] for c in allcalls) == sum(r["total_tokens"] for r in records), "AUTOSAR token ledger differs")
        prefix = member("formal_v20/generation/experiment_results.json")
        for name, value, pointer, unit in [
            ("auto.cases", len({r['case_id'] for r in grows}), "[*].case_id distinct", "base cases"),
            ("auto.repeats", len({r['repetition'] for r in grows}), "[*].repetition distinct", "runs/case"),
            ("auto.n", len(grows), "[*]", "runs"),
            ("auto.pass", sum(r['decision']=='PASS' for r in grows), "[*].decision=PASS", "runs"),
            ("auto.files", len(xmis), "[*].arxml_files; original artifact_hashes/ARXML", "ARXML files"),
            ("auto.xsd", sum(r['xsd_pass'] for r in grows), "[*].xsd_pass", "ARXML files"),
            ("auto.obligations", sum(r['structural_obligations'] for r in grows), "[*].structural_obligations", "checks"),
            ("auto.references", sum(r['local_references'] for r in grows), "[*].local_references", "checks"),
            ("auto.components", sum(r['component'] for r in xmis), "original Components/*.arxml", "files"),
            ("auto.interfaces", sum(not r['component'] for r in xmis), "original Interfaces/*.arxml", "files")]:
            metrics.add(name, value, genpath, pointer, code, unit, "auto.n" if name=='auto.pass' else None)
        metrics.add("auto.tokens", sum(c['usage']['total_tokens'] for c in allcalls), AUTOZIP,
                    "generation/runs/*/*/R*/repair-off/attempt-001/provider_calls.jsonl /usage/total_tokens", code, "tokens")
        metrics.add("auto.seconds.mean", statistics.mean(r['total_duration_seconds'] for r in records), AUTOZIP,
                    prefix + " /records/*/total_duration_seconds mean", code, "seconds/run", "auto.n")
        for key, vals in [("components.elements", [r['elements'] for r in xmis if r['component']]),
                          ("interfaces.elements", [r['elements'] for r in xmis if not r['component']]),
                          ("xml.depth", [r['depth'] for r in xmis])]:
            for op, fn in [("min", min), ("max", max)]:
                metrics.add("auto."+key+"."+op, fn(vals), AUTOZIP, "generation/runs/*/atlas_output/ARXML/*.arxml; element traversal", code, "XML elements" if 'elements' in key else "levels")
        largest = [r for r in xmis if r['case']=='ASW-FULL-06' and r['repeat']==1]
        metrics.add('auto.root_level',len([tree]),AUTOZIP,'original ARXML depth convention counts the single AUTOSAR root as the first level',code,'depth convention')
        metrics.add("auto.largest.elements", sum(r['elements'] for r in largest), AUTOZIP, "ASW-FULL-06/R1 original ARXML elements", code, "XML elements")
        metrics.add("auto.largest.files", len(largest), AUTOZIP, "ASW-FULL-06/R1 original ARXML", code, "files")
        req = obj("requirements/rendered/run_manifest.json")["validation"]
        for tier, count in Counter(r['tier'] for r in records if r['repetition']==1).items():
            metrics.add("auto.tier."+tier, count, AUTOZIP, "requirements/rendered/run_manifest.json /validation/tier_counts/"+tier, code, "base cases")
        for field in ['p_ports','r_ports','runnables','timing_events','variable_accesses']:
            metrics.add("auto.required."+field, sum(r['actual_counts'][field] for r in req['checked_cases']), AUTOZIP,
                        "requirements/rendered/run_manifest.json /validation/checked_cases/*/actual_counts/"+field, code, "required objects")
        for tier in ['standard','full']:
            cases = [r['actual_counts'] for r in req['checked_cases'] if ('STD' if tier=='standard' else 'FULL') in r['case_id']]
            for field, vals in [('ports',[r['p_ports']+r['r_ports'] for r in cases]),('runnables',[r['runnables'] for r in cases])]:
                for op, fn in [('min',min),('max',max)]:
                    metrics.add(f"auto.{tier}.{field}.{op}", fn(vals), AUTOZIP, "requirements/rendered/run_manifest.json /validation/checked_cases; tier filter", code)
        case_text = z.read(member("requirements/asw_cases_v3.yaml")).decode('utf-8-sig')
        initial_value = one(re.findall(r'unconnected_required_port_init_value:\s*([0-9.]+)', case_text), 'AUTOSAR initial value')
        metrics.add('auto.baseline.init', float(initial_value), AUTOZIP, 'requirements/asw_cases_v3.yaml /authoritative_context/unconnected_required_port_init_value', code, 'value')
        baseline = one((t for t in re.split(r'(?m)^  - case_id: ',case_text) if t.startswith('ASW-FULL-01\n')), 'baseline YAML')
        for key, regex in [('period',r'period_s:\s*([0-9.]+)'),('timeout',r'alive_timeout_s:\s*([0-9.]+)')]:
            vals = re.findall(regex,baseline)
            if vals: metrics.add('auto.baseline.'+key,float(vals[0]),AUTOZIP,'requirements/asw_cases_v3.yaml case_id=ASW-FULL-01; '+regex,code,'seconds' if key!='init' else 'value')
        metrics.alias('auto.baseline.period_ms',metrics.values['auto.baseline.period']['value']*1000,'auto.baseline.period','milliseconds')
        ev=one((e for r,e in zip(grows,evaluations) if r['case_id']=='ASW-FULL-01' and r['repetition']==1), 'worked AUTOSAR example')
        for key,field in [('obligations','structural_obligations'),('references','reference_integrity')]:
            metrics.add('auto.example.'+key,len(ev[field]),AUTOZIP,'generation/runs/gpt-5.6-luna/ASW-FULL-01/R1/repair-off/attempt-001/independent_evaluation.json /'+field,code,'checks')
        repairs = obj("formal_v20/repair/repair_results.json")['records']; rm={r['run_id']:r for r in repairs}
        require(set(rm)=={r['run_id'] for r in rrows},'AUTOSAR repair membership differs')
        for r in rrows:
            require(r['final_exact_baseline_bytes_and_filenames']==rm[r['run_id']]['exact_original_recovery'],'AUTOSAR restoration differs')
        for layer, alias in [('core_fixed_operator','core'),('substitution','sub')]:
            rr=[r for r in rrows if r['analysis_layer']==layer]
            source_rows=[r for r in repairs if r['analysis_layer']==layer]
            for field,value in [('n',len(rr)),('detected',sum(r['input_decision']=='FAIL' for r in rr)),('pass',sum(r['final_exact_baseline_bytes_and_filenames'] for r in rr))]:
                metrics.add(f'auto.repair.{alias}.{field}',value,reppath,'[*] analysis_layer='+layer+'; '+field,code,'repair units',f'auto.repair.{alias}.n' if field=='pass' else None)
            for field,srcfield in [('tokens','provider_audited_total_tokens'),('responses','provider_call_audit_count'),('rounds','repair_accepted_rounds')]:
                value=max(r[srcfield] for r in source_rows) if field=='rounds' else sum(r[srcfield] for r in source_rows)
                metrics.add(f'auto.repair.{alias}.{field}',value,AUTOZIP,'formal_v20/repair/repair_results.json /records/*/'+srcfield+' analysis_layer='+layer,code,field)
        for mutation in sorted({r['mutation'] for r in rrows}):
            rr=[r for r in rrows if r['mutation']==mutation]
            for field,value in [('n',len(rr)),('detected',sum(r['input_decision']=='FAIL' for r in rr)),('pass',sum(r['final_exact_baseline_bytes_and_filenames'] for r in rr))]:
                metrics.add('auto.mutation.'+mutation+'.'+field,value,reppath,'[*] mutation='+mutation+'; '+field,code,'repair units')
        constraints_path='experiments/vllm/runtime/AI_XmlGenerator/src/kg_builder/doc_constr_parser/v2/constraints_v2.json'
        constraints=read(root/constraints_path)
        metrics.add('icm.constraints',len(constraints),constraints_path,'/ (record count; unique IDs also checked)','inspection/check_icm_evidence.py','published records')
        require(len(constraints)==len({c['id'] for c in constraints}),'duplicate ICM IDs')
        ctx=obj('frozen_contract/FORMAL_NEO4J_CONTEXT.json')
        require(ctx['constraint_card_count']==len(constraints),'ICM card count differs from context')
        for name,key in [('links','constraint_link_count'),('nodes','schema_node_count'),('relationships','schema_relationship_count')]:
            metrics.add('icm.'+name,ctx[key],AUTOZIP,'frozen_contract/FORMAL_NEO4J_CONTEXT.json /'+key,'inspection/check_icm_evidence.py','retained graph count',level='RETAINED_CONTEXT_COUNT_NOT_GRAPH_REBUILD')
        plan=obj('code_snapshot/runtime_assets/src/generate_formal_constraints/v2/validation_plan.json')
        metrics.add('icm.rules',len(plan['rules']),AUTOZIP,'code_snapshot/runtime_assets/src/generate_formal_constraints/v2/validation_plan.json /rules','inspection/check_icm_evidence.py','configured rules')
        for backend,count in Counter(r['backend'] for r in plan['rules']).items():
            metrics.add('icm.rules.'+backend,count,AUTOZIP,'validation_plan.json /rules backend='+backend,'inspection/check_icm_evidence.py','configured rules')


def vllm(root, metrics):
    code='experiments/vllm/review.py'
    with tarfile.open(root/VLLMTAR,'r:gz') as z:
        names=z.getnames()
        def obj(name): return json.load(z.extractfile(name))
        original=[obj(n) for n in names if re.search(r'/formal_run_b1/\d+\.json$',n)]
        posts={r['schedule_ordinal']:r for r in [obj(n) for n in names if re.search(r'/formal_postprocess_local_v1/\d+\.json$',n)]}
        formal=obj(one((n for n in names if n.endswith('/FORMAL_RESULT.json')),'vLLM formal'))
        byarm={a:[r for r in original if r['schedule']['arm']==a] for a in ['U','G','A']}
        for arm,rows in byarm.items():
            values={'n':len(rows),'pass':sum(posts[r['schedule']['schedule_ordinal']]['end_to_end_structural_decision']=='PASS' for r in rows),
                    'tokens':sum(r['usage']['completion_tokens'] for r in rows),'seconds':sum(r['elapsed_seconds'] for r in rows)}
            require(values['pass']==formal['arm_summary'][arm]['end_to_end_structural_decision_pass_count'],'vLLM outcome aggregate differs')
            for key,value in values.items():
                metrics.add(f'vllm.{arm}.{key}',value,VLLMTAR,'formal_run_b1/*.json arm='+arm+'; formal_postprocess_local_v1/*.json /end_to_end_structural_decision',code,'seconds' if key=='seconds' else 'output tokens' if key=='tokens' else 'runs',f'vllm.{arm}.n' if key=='pass' else None)
            for key in ['tokens','seconds']:
                metrics.alias(f'vllm.{arm}.{key}.mean',values[key]/len(rows),f'vllm.{arm}.{key}',denominator=f'vllm.{arm}.n')
            for tier in ['minimal','standard','full']:
                rr=[r for r in rows if r['schedule']['tier']==tier]
                for key,value in [('n',len(rr)),('pass',sum(posts[r['schedule']['schedule_ordinal']]['end_to_end_structural_decision']=='PASS' for r in rr))]:
                    metrics.add(f'vllm.{arm}.{tier}.{key}',value,VLLMTAR,'formal_run_b1/*.json /schedule/tier='+tier+' /schedule/arm='+arm+'; postprocess result',code,'runs')
        metrics.add('vllm.total',len(original),VLLMTAR,'formal_run_b1/*.json',code,'generations')
        grouped=defaultdict(dict)
        for r in original: grouped[(r['schedule']['case_id'],r['schedule']['repetition'])][r['schedule']['arm']]=r
        delta=[v['A']['elapsed_seconds']-v['G']['elapsed_seconds'] for v in grouped.values()]
        for key,value in [('mean',statistics.mean(delta)),('median',statistics.median(delta))]:
            metrics.add('vllm.overhead.'+key,value,VLLMTAR,'formal_run_b1/*.json paired (case_id,repetition), A.elapsed_seconds-G.elapsed_seconds',code,'seconds')
        metrics.add('vllm.overhead.percent',(sum(r['elapsed_seconds'] for r in byarm['A'])/sum(r['elapsed_seconds'] for r in byarm['G'])-1)*100,VLLMTAR,'formal_run_b1/*.json sum(A.elapsed_seconds)/sum(G.elapsed_seconds)-1',code,'%')
        metrics.add('vllm.equal_pairs',sum(v['A']['output']==v['G']['output'] for v in grouped.values()),VLLMTAR,'formal_run_b1/*.json paired A.output == G.output',code,'pairs')
        n=one((n for n in names if 'structured-output-audit-' in n and n.endswith('.ndjson')),'vLLM audit')
        bounds=Counter();observed=0
        for line in z.extractfile(n):
            r=json.loads(line);event=r['event']
            if event['event_type']=='binding_step' and event['payload']['evaluable']:
                observed+=1;bounds[r['request_id']]+=int(event['payload']['bound'])
        for key,value in [('bound',sum(bounds.values())),('steps',observed),('bound_runs',sum(v>0 for v in bounds.values())),('bound.min',min(bounds.values())),('bound.max',max(bounds.values()))]:
            metrics.add('vllm.'+key,value,VLLMTAR,n+' /event/payload/{evaluable,bound}; group request_id',code,'decoding steps' if key in ['bound','steps'] else 'runs' if key=='bound_runs' else 'steps/run',level='RECOUNTED_RETAINED_FLAGS_NOT_LOGIT_RECOMPUTATION')
        metrics.alias('vllm.bound.percent',100*sum(bounds.values())/observed,'vllm.bound','%','vllm.steps')


def railway(root, metrics):
    path='experiments/railway/results/train_recomputed.json';rows=read(root/path)['rows']
    code='experiments/railway/corrected/replay_evidence.py'
    archives=[zipfile.ZipFile(p) for p in sorted((root/'experiments/railway/archives').glob('*.zip'))]
    try:
        members={n:(z,p) for z,p in zip(archives,sorted((root/'experiments/railway/archives').glob('*.zip'))) for n in z.namelist()}
        def obj(n): return json.loads(members[n][0].read(n))
        plan=obj('frozen/release/EXECUTION_PLAN.json');units={u['directory']:u for u in plan['units']}
        for stage in ['G','R','T','CLEAN']:
            paired=obj('frozen/release/formal_export/paired/'+stage+'.json')['records'];original={r['unit_id']:r for r in paired}
            for row in [r for r in rows if r['stage']==stage]: require(row['valid']==original[row['unit_id']]['outcome'],'Railway paired outcome differs')
            for arm in (['G0','GS','GF'] if stage=='G' else ['S','V','F']):
                rr=[r for r in rows if r['stage']==stage and r['arm']==arm]
                for key,value in [('n',len(rr)),('pass',sum(r['valid'] for r in rr))]:
                    metrics.add(f'rail.{stage}.{arm}.{key}',value,path,f'/rows stage={stage},arm={arm}; original paired/{stage}.json /records/*/outcome',code,'endpoints',f'rail.{stage}.{arm}.n' if key=='pass' else None)
        cases={u['base_scenario_id'] for u in plan['units']};seeds={u['seed'] for u in plan['units']}
        metrics.add('rail.cases',len(cases),path,'/rows/*/unit_id distinct base-task component',code,'base tasks')
        metrics.add('rail.repeats',len(seeds),path,'/rows/*/unit_id distinct seed component',code,'runs/task')
        metrics.add('rail.seed1',plan['parameters']['replicate_seeds']['1'],'experiments/railway/PAYLOAD_MANIFEST.json','frozen/release/EXECUTION_PLAN.json /parameters/replicate_seeds/1',code,'seed')
        metrics.alias('rail.G.GF.fail',metrics.values['rail.G.GF.n']['value']-metrics.values['rail.G.GF.pass']['value'],'rail.G.GF.n','endpoints')
        metrics.add('rail.CLEAN.inputs',len({u['base_scenario_id'] for u in plan['units'] if u['stage']=='CLEAN'}),'experiments/railway/PAYLOAD_MANIFEST.json','frozen/release/EXECUTION_PLAN.json /units stage=CLEAN distinct base_scenario_id',code,'inputs')
        inv_name=one((n for n in members if n.endswith('/INPUT_INVENTORY.json')),'railway input inventory')
        inventory=obj(inv_name)
        for kind,count in Counter(r['mutation_kind'] for r in inventory['mutations']).items():
            actual={u['unit_id'].split(':')[2] for u in plan['units'] if u['stage']=='R'}
            require(all(r['mutation_id'] in actual for r in inventory['mutations']),'Railway mutation inventory differs from executed inputs')
            metrics.add('rail.R.'+kind,count,'experiments/railway/PAYLOAD_MANIFEST.json',inv_name+' /mutations/*/mutation_kind='+kind,code,'fault inputs')
        gp=obj('frozen/release/formal_export/paired/G.json')['records']
        starts=[r for r in gp if r['unit_id'].endswith(':G0')]
        failed=[r for r in starts if not r['outcome']]
        metrics.add('rail.G.failed',len(failed),'experiments/railway/PAYLOAD_MANIFEST.json','frozen/release/formal_export/paired/G.json /records G0 outcome=false',code,'starting points')
        missing=sum(r.get('stop_reason') is None for r in failed)
        metrics.add('rail.G.missing',missing,'experiments/railway/PAYLOAD_MANIFEST.json','frozen/release/formal_export/paired/G.json /records G0 rejected before evaluation',code,'starting points')
        metrics.alias('rail.G.failed_models',len(failed)-missing,'rail.G.failed','models')
        for arm in ['GS','GF']:
            byid={r['unit_id'].rsplit(':',1)[0]:r for r in gp if r['unit_id'].endswith(':'+arm)}
            repaired=sum(byid[r['unit_id'].rsplit(':',1)[0]]['outcome'] for r in failed)
            metrics.add('rail.G.'+arm+'.recovered',repaired,'experiments/railway/PAYLOAD_MANIFEST.json','frozen/release/formal_export/paired/G.json paired G0=false, '+arm+'=true',code,'starting points')
        for reason,count in Counter(r.get('stop_reason') for r in gp if r['unit_id'].endswith(':GF') and not r['outcome']).items():
            if reason: metrics.add('rail.G.GF.stop.'+reason,count,'experiments/railway/PAYLOAD_MANIFEST.json','frozen/release/formal_export/paired/G.json GF outcome=false /stop_reason='+reason,code,'models')
        metrics.alias('rail.G.remaining_models',len(failed)-missing-metrics.values['rail.G.GF.recovered']['value'],'rail.G.failed','models')
        costs=defaultdict(Counter)
        for name,(z,p) in members.items():
            if name.startswith('frozen/release/paid_formal/units/') and name.endswith('/response.json'):
                rel=name.split('paid_formal/',1)[1]
                directory=one((d for d in units if rel.startswith(d+'/')),'response unit')
                u=units[directory];r=obj(name);c=costs[(u['stage'],u['arm'])]
                c['responses']+=1;c['tokens']+=r['usage']['total_tokens'];c['seconds']+=r['elapsed_seconds']
        for (stage,arm),c in costs.items():
            for key,value in c.items():
                metrics.add(f'rail.{stage}.{arm}.{key}',value,'experiments/railway/PAYLOAD_MANIFEST.json',f'archive members frozen/release/paid_formal/units/*/response.json; stage={stage},arm={arm}; /usage/total_tokens or /elapsed_seconds',code,key)
        for key in ['responses','tokens','seconds']:
            metrics.add('rail.total.'+key,sum(c[key] for c in costs.values()),'experiments/railway/PAYLOAD_MANIFEST.json','all original paid_formal/units/*/response.json /'+key,code,key)
        groups=defaultdict(list)
        for r in rows:
            if r['stage']=='R':
                _,task,fault,seed,arm=r['unit_id'].split(':');groups[(task,fault,arm)].append(r['valid'])
        for arm in ['S','V','F']:
            selected=[v for (t,f,a),v in groups.items() if a==arm];require(all(len(v)==len(seeds) for v in selected),'R repetition grouping differs')
            metrics.add('rail.R.'+arm+'.stable',sum(all(v) for v in selected),path,'/rows stage=R; group(base_task,fault_input,arm); all three valid',code,'fixed fault inputs','rail.R.inputs')
        metrics.add('rail.R.inputs',len({(t,f) for t,f,a in groups}),path,'/rows stage=R; distinct(base_task,fault_input)',code,'fixed fault inputs')
        stats=read(root/'experiments/railway/results/train_statistics_audit.json')
        stats_path='experiments/railway/corrected/replay_statistics.py'
        stats_code=(root/stats_path).read_text()
        draws=int(one(re.findall(r'range\((\d+)\)',stats_code),'railway bootstrap draw count'))
        tail=one(re.findall(r'for p in \[([^]]+)\]',stats_code),'railway interval quantiles')
        quantiles=[float(p) for p in tail.split(',')]
        metrics.add('rail.stats.draws',draws,stats_path,'range() bootstrap count',stats_path,'resamples',level='EXECUTED_STATISTICAL_PROTOCOL')
        metrics.add('rail.stats.confidence',100*(quantiles[1]-quantiles[0]),stats_path,'difference between interval quantiles',stats_path,'%',level='EXECUTED_STATISTICAL_PROTOCOL')
        for stage,comparisons in [('G',['GF-G0','GF-GS']),('R',['F-S','F-V'])]:
            cells=defaultdict(lambda:defaultdict(list))
            for r in rows:
                if r['stage']==stage: cells[r['unit_id'].split(':')[1]][r['arm']].append(int(r['valid']))
            case_means={c:{a:statistics.mean(v) for a,v in arms.items()} for c,arms in cells.items()}
            names=sorted(case_means);rng=random.Random(int(one(re.findall(r'Random\((\d+)\)',stats_code),'railway bootstrap seed')))
            distributions={c:[] for c in comparisons}
            for _ in range(draws):
                sample=[rng.choice(names) for _ in names]
                for c in comparisons:
                    a,b=c.split('-');distributions[c].append(statistics.fmean(case_means[n][a]-case_means[n][b] for n in sample))
            for comparison in comparisons:
                a,b=comparison.split('-');ra=[r['valid'] for r in rows if r['stage']==stage and r['arm']==a];rb=[r['valid'] for r in rows if r['stage']==stage and r['arm']==b]
                est=sum(ra)/len(ra)-sum(rb)/len(rb);v=stats[stage][comparison]
                require(abs(est-v['estimate'])<1e-12,'Railway difference differs')
                metrics.add(f'rail.{stage}.{comparison}.diff',est*100,path,f'/rows stage={stage}; proportion({a})-proportion({b})',code,'percentage points')
                for side,index in [('lo',0),('hi',1)]:
                    ordered=sorted(distributions[comparison]);pos=quantiles[index]*(len(ordered)-1);i=math.floor(pos);bound=ordered[i]+(pos-i)*(ordered[min(i+1,len(ordered)-1)]-ordered[i])
                    require(abs(bound-v['interval'][index])<1e-12,'Railway independently resampled interval differs')
                    metrics.add(f'rail.{stage}.{comparison}.{side}',bound*100,path,f'/rows paired base task resampling {stage}/{comparison}, quantile={quantiles[index]}',stats_path,'percentage points')
        tpath='experiments/railway_terra/reports/paired_tasks.csv';paired=list(csv.DictReader((root/tpath).read_text().splitlines()))
        parts=read(root/'experiments/railway_terra/PARTS_MANIFEST.json')
        joined=b''.join((root/'experiments/railway_terra'/p['path']).read_bytes() for p in parts['parts'])
        with zipfile.ZipFile(io.BytesIO(joined)) as z:
            final=json.loads(z.read('ATLAS_TERRA_SUPPLEMENT/continuation3/run/RESULTS.json'))
            summary=read(root/'experiments/railway_terra/reports/CURRENT_RESULTS_SUMMARY.json')
            require(sha(z.read('ATLAS_TERRA_SUPPLEMENT/continuation3/run/RESULTS.json'))==summary['source_results_sha256'],'Terra summary source hash differs')
            for model in ['Luna','Terra']:
                for arm in ['G0','GS','GF']:
                    count=sum(str(r[model+'_'+arm]).lower() in ['1','true'] for r in paired)
                    require(count==summary['complete_task_scope_successes'][model][arm],'Terra paired count differs')
                    if model=='Terra': require(count==final['groups'][arm]['strict_success'],'Terra original final RESULTS count differs')
                    metrics.add(f'terra.{model}.{arm}.pass',count,tpath,'/'+model+'_'+arm+' true count; final RESULTS comparison','experiments/railway_terra/source/review/continuation2/endpoint_review.py','successful tasks','terra.n')
                    metrics.alias(f'terra.{model}.{arm}.pct',100*count/len(paired),f'terra.{model}.{arm}.pass','%','terra.n')
            metrics.add('terra.n',len(paired),tpath,'distinct task_id','experiments/railway_terra/review.py','base tasks')
            endpoint_counts=Counter((r['task_id'],r['arm']) for r in final['rows'])
            require(len(set(endpoint_counts.values()))==1,'Terra repeated endpoints differ')
            metrics.add('terra.repeats',next(iter(endpoint_counts.values())),'experiments/railway_terra/PARTS_MANIFEST.json','ATLAS_TERRA_SUPPLEMENT/continuation3/run/RESULTS.json /rows count per(task_id,arm)','experiments/railway_terra/review.py','runs/task')
            prefix='ATLAS_TERRA_SUPPLEMENT/continuation3/run/tasks/'
            responses=[json.loads(z.read(n)) for n in z.namelist() if n.startswith(prefix) and n.endswith('/response.json')]
            for key,value in [('responses',len(responses)),('input',sum(r['usage']['prompt_tokens'] for r in responses)),('output',sum(r['usage']['completion_tokens'] for r in responses)),('tokens',sum(r['usage']['prompt_tokens']+r['usage']['completion_tokens'] for r in responses))]:
                metrics.add('terra.'+key,value,'experiments/railway_terra/PARTS_MANIFEST.json',prefix+'*/response.json /usage','experiments/railway_terra/source/review/continuation3/verify_final.py','tokens' if key!='responses' else 'responses')
    finally:
        for z in archives: z.close()


def pil_metrics(root, metrics):
    replay=pil.replay(root,statistics=True)
    path='experiments/pil/frozen/formal/PIL_V41_RUN_LEDGER.jsonl';code='inspection/check_pil_decision_flow.py'
    for arm,values in replay['arms'].items():
        for key,value in values.items():
            metrics.add('pil.'+arm+'.'+key,value,path,'rows arm='+arm+'; raw_text -> regenerated final record -> '+key,code,'tokens' if key=='tokens' else 'records','pil.'+arm+'.units' if key.endswith('valid') or key in ['system_release','gold_correct','endpoint_success'] else None)
            if key in ['structure_valid','common_delivery_valid','system_release','gold_correct','endpoint_success']:
                metrics.alias('pil.'+arm+'.'+key+'.pct',100*value/values['units'],'pil.'+arm+'.'+key,'%','pil.'+arm+'.units')
        metrics.alias('pil.'+arm+'.tokens.mean',values['tokens']/values['units'],'pil.'+arm+'.tokens','tokens/unit','pil.'+arm+'.units')
        metrics.add('pil.'+arm+'.f1',replay['summary']['arms'][arm]['citation_f1'],path,'raw final legal_basis versus corrected accepted_evidence; citation F1 mean',code,'F1')
    scored=replay['scored_units'];p3=[r for r in scored if r['arm']=='p3'];repairs=[r for r in p3 if r['repair_attempted']]
    for key,value in [('cases',len({r['case_id'] for r in scored})),('total',len(scored)),('repeats',len({r['replicate'] for r in scored})),('repairs',len(repairs)),('recovered',sum(r.get('repair_recovered_correctness',False) for r in repairs)),('induced',sum(r.get('repair_induced_error',False) for r in repairs)),('repaired_endpoint',sum(r['endpoint_success'] for r in repairs)),('withheld',sum(not r['system_release'] for r in p3))]:
        metrics.add('pil.'+key,value,path,'replayed scored_units; '+key,code,'cases' if key=='cases' else 'runs/case' if key=='repeats' else 'records')
    metrics.add('pil.kb',len(pil.jsonl(root/'experiments/pil/frozen/prepaid_freeze/kb/authoritative_provisions_v41_en.jsonl')),'experiments/pil/frozen/prepaid_freeze/kb/authoritative_provisions_v41_en.jsonl','line count',code,'provision paraphrases')
    for comparison,result in replay['summary']['contrasts'].items():
        v=result['case_clustered_bootstrap']
        for key,value in [('diff',v['estimate']),('lo',v['ci95'][0]),('hi',v['ci95'][1])]:
            metrics.add('pil.'+comparison+'.'+key,100*value,path,'case means of raw-answer-derived endpoint; 20000 paired bootstrap draws, seed 20260902; '+comparison,code,'percentage points')
    metrics.add('pil.p3-p2.extra',replay['arms']['p3']['endpoint_success']-replay['arms']['p2']['endpoint_success'],path,'P3.endpoint_success-P2.endpoint_success',code,'records')
    ci_key=one((k for k in next(iter(replay['summary']['contrasts'].values()))['case_clustered_bootstrap'] if re.fullmatch(r'ci\d+',k)),'PIL confidence key')
    metrics.add('pil.stats.confidence',int(ci_key[2:]),path,'PIL pure scorer paired interval '+ci_key+' protocol',code,'%',level='EXECUTED_STATISTICAL_PROTOCOL')


def collect(root):
    m=Metrics();autosar(root,m);vllm(root,m);railway(root,m);pil_metrics(root,m)
    return m.values


def numbers(text):
    text=re.sub(r'\\(?:paperref|ref|label|texttt)\{[^}]*\}','',text)
    text=text.replace('--',' ').replace(r'\ensuremath{-}','-').replace(r'\_','_')
    text=re.sub(r'\b(?:constr_\d+|TPS_SWCT_\d+|ASW-(?:FULL|MIN|STD)-\d+|MIN-\d+|BAL-\d+-\d+|[PGLF]\d+)\b','',text)
    text=re.sub(r'gpt-[\w.\-]+|Qwen[\w.\-]+|\bcase\d+\b','',text)
    return re.findall(r'(?<![\w])[-+]?\d+(?:,\d{3})*(?:\.\d+)?',text)


def matches(printed, value):
    p=Decimal(printed.replace(',','').lstrip('+'));v=Decimal(str(value))
    return p == v.quantize(Decimal(1).scaleb(p.as_tuple().exponent),rounding=ROUND_HALF_UP)


def check_text(text, spec, metrics):
    findings=[];covered=[];tables={}
    for match in re.finditer(r'\\begin\{table\*?\}.*?\\end\{table\*?\}',text,re.S):
        label=one(re.findall(r'\\label\{(tab:[^}]+)\}',match.group()),'table label')
        tables[label]=(match.group(),text[:match.start()].count('\n')+1)
    require(set(tables)==set(spec['tables']),'Table inventory differs; unclassified new/missing table')
    for label,entry in spec['tables'].items():
        body,line=tables[label]
        if entry['kind']=='nonnumeric':
            covered.append(dict(label=label,line=line,kind=entry['reason']));continue
        matched_offsets=set()
        for row in entry['rows']:
            candidates=[(i,s) for i,s in enumerate(body.splitlines()) if re.search(row['pattern'],s)]
            require(len(candidates)==1,label+' row locator ambiguous/missing: '+row['pattern'])
            offset,content=candidates[0]
            matched_offsets.add(offset)
            printed=numbers(content if row.get('all_cells',False) else content.split('&',1)[-1])
            refs=row['metrics']; require(len(printed)==len(refs),label+' number coverage differs: '+row['pattern']+' '+str(printed)+' vs '+str(refs))
            for value,name in zip(printed,refs):
                require(name in metrics,'Unknown metric '+name)
                record=dict(label=label,line=line+offset,printed=value,metric=name,**metrics[name])
                record['status']='PASS' if matches(value,metrics[name]['value']) else 'FAIL'
                findings.append(record)
        for offset,content in enumerate(body.splitlines()):
            if ('&' in content or content.startswith(r'\caption')) and numbers(content):
                require(offset in matched_offsets,label+' unclassified numerical table row: '+content)
        covered.append(dict(label=label,line=line,kind='numeric rows checked',rows=len(entry['rows'])))
    for entry in spec['prose']:
        found=[(i+1,s) for i,s in enumerate(text.splitlines()) if re.search(entry['pattern'],s)]
        if not found and entry.get('optional'): continue
        require(len(found)==entry.get('occurrences',1),'Prose locator missing/ambiguous: '+entry['pattern'])
        for line,content in found:
            if 'capture' in entry:
                match=re.search(entry['capture'],content);require(match is not None,'Prose capture missing')
                printed=list(match.groups())
            else: printed=numbers(content)
            require(len(printed)==len(entry['metrics']),'Prose number coverage differs: '+entry['pattern']+' '+str(printed))
            for value,name in zip(printed,entry['metrics']):
                record=dict(label=entry['label'],line=line,printed=value,metric=name,**metrics[name])
                record['status']='PASS' if matches(value,metrics[name]['value']) else 'FAIL';findings.append(record)
    return dict(status='FAIL' if any(r['status']=='FAIL' for r in findings) else 'PASS',table_inventory=covered,
                checked_numeric_occurrences=len(findings),checks=findings)


def link(path,line=None):
    return GITHUB+urllib.parse.quote(path,safe='/')+(('#L'+str(line)) if line else '')


def markdown(report):
    out=['# Manuscript data cross-check','',
         'This index connects each checked number to its manuscript location, data selector, and recomputation code. Counts and costs are aggregated from retained original records. Native XSD/EMF/VIATRA validity is checked separately by the release verifier. No new model requests are made.','',
         '**Coverage.** All 19 tables are inventoried. Tables 1–3 are method tables; A2, C1 and D1 describe preparation, rules or conditions and contain no outcome measurements. All numerical rows of the remaining 13 tables, including caption/header denominators where applicable, and the specified principal numbers in the abstract, introduction, results, appendices and conclusion are checked. Citation numbers, section/algorithm labels, legal article identifiers, model-name digits, and illustrative object IDs are not experimental measurements. The machine-readable mapping makes the covered prose occurrences explicit; it is not a blanket verification of every numeral or every scientific claim.','',
         '**ICM scope.** The 1,085 constraint records are counted in the published JSON and cross-checked against the frozen context card count. The 6,533 links, 11,177 nodes and 14,106 relationships are retained Neo4j context counts. This check does not rebuild Neo4j or independently enumerate those graph objects. Configured checking-rule counts are not per-task executed-check counts.','',
         '**Decoding scope.** Intervention totals are recounted from retained `binding_step` flags. Historical logits and masks are not regenerated.','',
         'Status: **'+report['status']+'**. Checked numerical occurrences: '+str(report['checked_numeric_occurrences'])+'.','',
         '| Paper location | Printed number | Quantity, unit and denominator | Evidence selector | Code | Result |',
         '|---|---:|---|---|---|---|']
    for r in report['checks']:
        quantity=r['metric']+'; '+r['unit']+('; denominator '+str(r['denominator']) if r['denominator'] else '')
        selector=r['selector'].replace('|','\\|')
        out.append(f"| [{r['label']}]({link(MANUSCRIPT,r['line'])}) | {r['printed']} | {quantity} | [source]({link(r['source'])}) `{selector}`; {r['evidence_level']} | [code]({link(r['code'])}) | {r['status']} |")
    out+=['','## Table inventory','', '| Label | Classification |','|---|---|']
    out += [f"| [{r['label']}]({link(MANUSCRIPT,r['line'])}) | {r['kind']} |" for r in report['table_inventory']]
    out+=['','Archive-member selectors identify a member inside the linked archive, rather than a separate GitHub file. Machine reports also retain unrounded values. The paper checker itself is [check_paper_data.py]('+link('inspection/check_paper_data.py')+'), with [field mappings]('+link('inspection/paper_data_spec.json')+').','']
    return '\n'.join(out)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--paper',type=Path,help='Optional manuscript copy, including negative controls')
    p.add_argument('--output',type=Path,help='External machine JSON output; stdout by default')
    p.add_argument('--markdown',type=Path,help='Optional author-maintenance output for the navigation Markdown; no file is written by default. Reviewers should select an external path.')
    p.add_argument('--self-test',action='store_true')
    args=p.parse_args();root=args.root.resolve()
    try:
        spec=read(Path(__file__).with_name('paper_data_spec.json'));metrics=collect(root)
        paper=args.paper or root/MANUSCRIPT;text=paper.read_text(encoding='utf-8-sig')
        report=check_text(text,spec,metrics);report['manuscript_sha256']=sha(paper.read_bytes())
        for entry in report['checks']:
            for field in ['source','code']:
                require((root/entry[field]).is_file(),'Navigation target missing: '+entry[field])
            require(1 <= entry['line'] <= len(text.splitlines()),'Manuscript navigation line out of range')
        report['metric_count']=len(metrics);report['new_model_calls']=0
        if args.self_test:
            altered=text.replace('11,967,476','11,967,477',1)
            require(altered!=text,'Negative-control target missing')
            bad=check_text(altered,spec,metrics)
            require(bad['status']=='FAIL','Altered manuscript number was not rejected')
            report['negative_control']={'changed':'11,967,476 -> 11,967,477 in one manuscript occurrence','status':'EXPECTED_FAIL','failing_metrics':[r['metric'] for r in bad['checks'] if r['status']=='FAIL']}
    except Exception as error:
        report={'status':'FAIL','error':type(error).__name__+': '+str(error)}
    content=json.dumps(report,ensure_ascii=False,indent=2)
    if args.output:
        require(not args.output.resolve().is_relative_to(root),'Machine output must be outside the release')
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(content+'\n',encoding='utf-8')
    if args.markdown and 'checks' in report:
        args.markdown.parent.mkdir(parents=True,exist_ok=True);args.markdown.write_text(markdown(report),encoding='utf-8')
    print(content if not args.output else json.dumps({k:v for k,v in report.items() if k not in ['checks','table_inventory']},ensure_ascii=False,indent=2))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
