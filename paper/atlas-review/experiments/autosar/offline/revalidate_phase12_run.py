"""Offline saved-artifact verifier, added 2026-09-09.

The saved Phase 1 design is post-intervention. Nothing here calls a model,
reconstructs a missing raw response, or claims to reproduce the original calls.
Frozen validation/evaluation source bytes are imported from the extracted archive.
"""
from pathlib import Path
import importlib.util
import sys

from post_run_correction_identity import read_json, write_json


class OfflineVerifier:
    def __init__(self, release, runtime):
        self.release = Path(release)
        self.runtime = Path(runtime)
        sys.path[:0] = [str(self.runtime), str(self.release/'requirements')]
        from src.validation.v2.service import GeneratedArxmlValidationService
        from src.validation.v2.selection_obligations import validate_selection_obligations
        from lxml import etree
        self.etree = etree
        self.selection_check = validate_selection_obligations
        self.service = GeneratedArxmlValidationService.from_config(None)
        spec = importlib.util.spec_from_file_location('frozen_asw_evaluator', self.release/'code_snapshot/experiment/evaluate_asw_v3_run.py')
        self.evaluator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.evaluator
        spec.loader.exec_module(self.evaluator)
        # Original evaluator source stays byte-identical. Only runtime roots change.
        self.evaluator.ATLAS_ROOT = self.runtime
        self.evaluator.CASES_ROOT = self.release/'requirements'
        self.evaluator.XSD = self.runtime/'src/validation/data/AUTOSAR_4-2-2.xsd'

    def bundle(self, paths):
        result = {'components':{}, 'interfaces':{}}
        for kind, files in paths.items():
            for path in files:
                tree = self.etree.parse(str(path))
                names = tree.xpath('/a:AUTOSAR/a:AR-PACKAGES/a:AR-PACKAGE/a:ELEMENTS/*/a:SHORT-NAME/text()', namespaces={'a':'http://autosar.org/schema/r4.0'})
                # Missing document SHORT-NAME is one controlled corruption.
                name = names[0] if names else path.stem
                if name in result[kind]:
                    raise ValueError('Duplicate artifact identity: '+name)
                result[kind][name] = path.read_text(encoding='utf-8')
        return result

    def context(self, saved):
        return self.service.build_validation_context(
            saved.get('selection_scopes') or {},
            declared_use_cases=saved.get('declared_use_cases') or [],
            declared_constraint_ids=saved.get('declared_constraint_ids') or [],
            declared_targets=saved.get('declared_targets') or {},
            declared_parameters=saved.get('declared_parameters') or {},
            intent_scope=saved.get('intent_scope') or 'partial',
            declared_capability_scopes=saved.get('declared_capability_scopes') or [],
            manual_evidence_scope=saved.get('manual_evidence_scope'))

    def validate(self, case_id, paths, saved_context, report_dir, *, plans=None, prefix=''):
        if len(paths['components']) != 1:
            raise ValueError('Expected one component per V20 run bundle')
        bundle = self.bundle(paths)
        validation = self.service.validate_bundle(bundle, validation_context=self.context(saved_context))
        vp = Path(report_dir)/(prefix+'validation.json')
        write_json(vp, validation)
        evaluation = self.evaluator.evaluate(case_id=case_id, component_path=paths['components'][0], interface_paths=paths['interfaces'], validation_path=vp)
        write_json(Path(report_dir)/(prefix+'evaluation.json'), evaluation)
        selection = self.selection_check(bundle, plans) if plans is not None else None
        if selection is not None:
            write_json(Path(report_dir)/(prefix+'saved_plan_consistency.json'), selection)
        return validation, evaluation, selection
