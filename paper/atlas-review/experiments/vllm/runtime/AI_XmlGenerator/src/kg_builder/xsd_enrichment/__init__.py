"""Non-destructive XSD content-model enrichment for ATLAS metadata."""

from .content_model import XsdContentModelExtractor
from .matcher import MetadataMatcher, build_enriched_metadata

__all__ = [
    "MetadataMatcher",
    "XsdContentModelExtractor",
    "build_enriched_metadata",
]
