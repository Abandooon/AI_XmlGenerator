# -*- coding: utf-8 -*-
"""
混合校验脚本（参考 SMTValidator / SHACLValidator 的分流与输出风格）：
- 读取 input/ 下的 RDF/XML（.rdf/.xml/.owl/.rdfxml）
- 直接进行“等价于 SHACL 的”局部/结构/格式/关系/基数检查（Violation/Warning/Info）
- 尝试运行一个 precedence 的 SMT 小示例（有 z3 则执行，无 z3 则提示跳过）
- 控制台输出逐条结果与汇总
"""
import re
import sys
from pathlib import Path

from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF

EX = Namespace("http://example.org/autosar#")

ALLOWED_METHOD_CATS = {"SCALE_LINEAR_AND_TEXTTABLE","SCALE_RATIONAL_AND_TEXTTABLE","TEXTTABLE","BITFIELD_TEXTTABLE"}
RECOMMENDED_UNITGROUP_CATS = {"COUNTRY","CALCULATION","EQUIV_UNITS"}
TYPEDEF_REGEX = re.compile(r'^[A-Za-z_][A-Za-z0-9_\s\*\[\]\(\),]*;$')

def objects(g, s, p):
    for _, _, o in g.triples((s, p, None)):
        yield o

def subjects(g, p, o):
    for s, _, _ in g.triples((None, p, o)):
        yield s

def first_literal(g, s, p):
    for o in objects(g, s, p):
        if isinstance(o, Literal):
            return str(o)
    return None

def check_constr_1146(g):
    """CompuScale.symbol 仅在允许类别的 CompuMethod 下出现（Violation）"""
    count_ok = 0; errs = []
    for cs, _, _ in g.triples((None, RDF.type, EX.CompuScale)):
        has_sym = any(True for _ in objects(g, cs, EX.symbol))
        if not has_sym:
            continue
        m = next(objects(g, cs, EX.hasCompuMethod), None)
        cat = (first_literal(g, m, EX.category) if m else None)
        if cat not in ALLOWED_METHOD_CATS:
            errs.append(f"[ERROR] [constr_1146] symbol present but category not allowed (category={cat}) -> node={cs}")
        else:
            count_ok += 1
    return errs, count_ok

def check_constr_1135(g):
    """BITFIELD_TEXTTABLE 下 vt 不含 '|'（Violation）"""
    errs = []; ok = 0
    for c, _, _ in g.triples((None, RDF.type, EX.CompuConstTextContent)):
        vt = first_literal(g, c, EX.vt)
        m = next(objects(g, c, EX.belongsToMethod), None)
        mcat = first_literal(g, m, EX.category) if m else None
        if mcat == "BITFIELD_TEXTTABLE" and vt is not None and "|" in vt:
            errs.append(f"[ERROR] [constr_1135] vt contains '|' under BITFIELD_TEXTTABLE -> node={c}")
        else:
            ok += 1
    return errs, ok

def check_unitgroup_recommend(g):
    """UnitGroup.category 推荐集合（Warning）"""
    warns = []; ok = 0
    for ug, _, _ in g.triples((None, RDF.type, EX.UnitGroup)):
        cat = first_literal(g, ug, EX.category)
        if cat and cat not in RECOMMENDED_UNITGROUP_CATS:
            warns.append(f"[WARN ] [UnitGroup] category '{cat}' not in recommended set -> node={ug}")
        else:
            ok += 1
    return warns, ok

def check_TPS_SWCT_01061(g):
    """
    单位换算：
      - physicalDimension 必须相等（Violation）
      - 若源组 category=EQUIV_UNITS，优先同组（Warning）
    """
    errs = []; warns = []; ok = 0
    for src, _, tgt in g.triples((None, EX.convertTo, None)):
        d1 = first_literal(g, src, EX.physicalDimension)
        d2 = first_literal(g, tgt, EX.physicalDimension)
        if d1 is not None and d2 is not None and d1 != d2:
            errs.append(f"[ERROR] [TPS_SWCT_01061] conversion dimension mismatch {d1} -> {d2} (src={src}, tgt={tgt})")
        else:
            ok += 1
        gsrc = next(objects(g, src, EX.inUnitGroup), None)
        gcat = first_literal(g, gsrc, EX.category) if gsrc else None
        gtgt = next(objects(g, tgt, EX.inUnitGroup), None)
        if gcat == "EQUIV_UNITS" and gsrc != gtgt:
            warns.append(f"[WARN ] [TPS_SWCT_01061] prefer target in same UnitGroup (category=EQUIV_UNITS) (src={src}, tgt={tgt})")
    return errs, warns, ok

def check_constr_1141(g):
    """出现 VariableAccess.scope 时，必须被允许的 RunnableEntity 角色引用（Violation）"""
    errs = []; ok = 0
    allowed_roles = [EX.dataReadAccess, EX.dataWriteAccess, EX.dataSendPoint, EX.dataReceivePointByValue, EX.dataReceivePointByArgument]
    for va, _, _ in g.triples((None, RDF.type, EX.VariableAccess)):
        sc = first_literal(g, va, EX.scope)
        if sc is None:
            ok += 1
            continue
        referenced = any(True for role in allowed_roles for _ in subjects(g, role, va))
        if not referenced:
            errs.append(f"[ERROR] [constr_1141] VariableAccess.scope present but not referenced by allowed RunnableEntity roles -> node={va}")
        else:
            ok += 1
    return errs, ok

def check_constr_2006(g):
    """每个 AsynchronousServerCallPoint 恰好被 1 个 ResultPoint 引用（Violation）"""
    errs = []; ok = 0
    callpoints = [cp for cp, _, _ in g.triples((None, RDF.type, EX.AsynchronousServerCallPoint))]
    for cp in callpoints:
        cnt = sum(1 for _ in subjects(g, EX.resultOf, cp))
        if cnt != 1:
            errs.append(f"[ERROR] [constr_2006] CallPoint referenced by {cnt} ResultPoint(s) (expected 1) -> node={cp}")
        else:
            ok += 1
    return errs, ok

def check_typedef(g):
    """PerInstanceMemory.typeDefinition 近似 C 声明；以 ';' 结束（Violation）"""
    errs = []; ok = 0
    for pim, _, _ in g.triples((None, RDF.type, EX.PerInstanceMemory)):
        td = first_literal(g, pim, EX.typeDefinition)
        if not (td and TYPEDEF_REGEX.match(td)):
            errs.append(f"[ERROR] [PerInstanceMemory.typeDefinition] Not a simple C-like declaration ending with ';' -> node={pim}, value={td!r}")
        else:
            ok += 1
    return errs, ok

def try_run_smt_precedence_demo():
    """
    precedence 的一个极简 SMT 演示：
      - 三个候选来源 pick_SDDP, pick_IVT, pick_AICM，恰好选一个
      - 偏好：IVT 不与 AICM 同时成立（示意优先/互斥）
    有 z3 则实际求解；没有则提示跳过（与 SMTValidator 行为一致）。
    """
    try:
        import z3  # 若不可用会抛异常
    except Exception:
        print("[SKIP ] SMT precedence demo skipped (z3 not available)")
        return {"status": "skipped", "detail": "z3 not available"}

    # 建模
    pick_SDDP, pick_IVT, pick_AICM = z3.Bools('pick_SDDP pick_IVT pick_AICM')
    s = z3.Solver()
    s.add(z3.PbEq([(pick_SDDP,1),(pick_IVT,1),(pick_AICM,1)], 1))  # 恰好选一个
    s.add(z3.Implies(pick_IVT, z3.Not(pick_AICM)))                # 偏好/互斥示意
    # （可扩展：把“有效值 eff”等式绑定到被选来源）

    res = s.check()
    if res == z3.sat:
        m = s.model()
        chosen = [n for n in ["pick_SDDP","pick_IVT","pick_AICM"] if z3.is_true(m.eval(z3.Bool(n)))]
        print(f"[OK   ] SMT precedence demo: SAT, chosen={chosen}")
        return {"status":"sat","chosen":chosen}
    else:
        print(f"[ERROR] SMT precedence demo: {res}")
        return {"status":str(res)}

def validate_file(path: Path):
    g = Graph()
    g.parse(str(path))
    print(f"\n=== File: {path.name} ===")

    violations = 0
    warnings   = 0

    # —— 等价 SHACL 的直接检查 ——（按“Violation/Warning/Info”输出）
    for fn in [check_constr_1146, check_constr_1135, check_constr_2006, check_constr_1141, check_typedef]:
        errs, ok = fn(g)
        for e in errs:
            print(e); violations += 1
        if not errs:
            print(f"[OK   ] {fn.__name__} (Violation)")

    # UnitGroup 推荐 & 单位换算（含 Warning）
    warns, ok = check_unitgroup_recommend(g)
    for w in warns:
        print(w); warnings += 1
    if not warns:
        print(f"[OK   ] UnitGroup recommended categories (Warning)")

    errs, warns2, ok = check_TPS_SWCT_01061(g)
    for e in errs:
        print(e); violations += 1
    for w in warns2:
        print(w); warnings += 1
    if not errs:
        print(f"[OK   ] TPS_SWCT_01061 physicalDimension equality (Violation)")
    if not warns2:
        print(f"[OK   ] TPS_SWCT_01061 group preference (Warning)")

    # Info（示例）
    print("[INFO ] [TPS_SWCT_01326] VariableAccess.scope constrains communication scope (informational).")

    # —— precedence 的 SMT 小演示（可选）——
    try_run_smt_precedence_demo()

    print(f"[SUMMARY] violations={violations}, warnings={warnings}")

def main():
    # 1) 若传了参数就用参数；否则默认用脚本同级的 input/
    if len(sys.argv) >= 2:
        indir = Path(sys.argv[1])
    else:
        indir = (Path(__file__).parent / "input").resolve()
        print(f"[INFO ] No <input_dir> arg provided, default to: {indir}")

    if not indir.exists():
        print(f"Input directory not found: {indir}")
        sys.exit(1)

    # 2) 扫描 RDF/XML
    rdf_files = sorted([p for p in indir.iterdir()
                        if p.suffix.lower() in (".rdf", ".xml", ".owl", ".rdfxml")])
    if not rdf_files:
        print("No RDF/XML files found in input/")
        sys.exit(1)

    # 3) 逐个验证并输出到控制台
    for p in rdf_files:
        validate_file(p)

if __name__ == "__main__":
    main()

