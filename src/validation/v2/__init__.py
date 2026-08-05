"""Reference-aware, fail-closed ARXML validation runtime."""

from . import additional_plugins as _additional_plugins
from . import advanced_local_plugins as _advanced_local_plugins
from . import cardinality_and_usecase_plugins as _cardinality_and_usecase_plugins
from . import cross_consistency_plugins as _cross_consistency_plugins
from . import dsl as _dsl
from . import intent_naming_plugins as _intent_naming_plugins
from . import local_semantic_plugins as _local_semantic_plugins
from . import nvrm_value_plugins as _nvrm_value_plugins
from . import ordering_plugins as _ordering_plugins
from . import qualified_plugins as _qualified_plugins
from . import reference_semantics as _reference_semantics
from . import relation_plugins as _relation_plugins
from . import remaining_graph_plugins as _remaining_graph_plugins
from . import remaining_reference_plugins as _remaining_reference_plugins
from . import remaining_structural_plugins as _remaining_structural_plugins
from . import remaining_type_plugins as _remaining_type_plugins
from . import semantic_graph_plugins as _semantic_graph_plugins
from . import type_semantics_plugins as _type_semantics_plugins
from . import value_and_local_plugins as _value_and_local_plugins
from . import vsa_profile_plugins as _vsa_profile_plugins
from .context import ValidationContextError, build_validation_context
from .engine import ValidationEngine
from .repair_loop import BundleRepairLoop
from .service import GeneratedArxmlValidationService

__all__ = [
    "BundleRepairLoop",
    "GeneratedArxmlValidationService",
    "ValidationContextError",
    "ValidationEngine",
    "build_validation_context",
]
