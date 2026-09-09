"""Lossless, bounded token-id evidence for exact ATLAS response replay."""

from __future__ import annotations

import base64
import hashlib
import json
import zlib
from collections.abc import Mapping, Sequence
from typing import Any

TOKEN_EVIDENCE_SCHEMA_VERSION = "atlas.token_ids.evidence.v1"
TOKEN_EVIDENCE_ENCODING = "base64+zlib+canonical-json"
MAX_TOKEN_COUNT = 1_000_000
MAX_CANONICAL_BYTES = 16 * 1024 * 1024


def _normalise_token_ids(token_ids: Sequence[int]) -> list[int]:
    if isinstance(token_ids, (str, bytes, bytearray)):
        raise ValueError("token_ids_must_be_a_sequence_of_integers")
    normalised: list[int] = []
    for token_id in token_ids:
        if isinstance(token_id, bool) or not isinstance(token_id, int):
            raise ValueError("token_ids_must_be_integers")
        if token_id < 0:
            raise ValueError("token_ids_must_be_nonnegative")
        normalised.append(token_id)
    if len(normalised) > MAX_TOKEN_COUNT:
        raise ValueError("token_id_count_exceeds_evidence_limit")
    return normalised


def _canonical_bytes(token_ids: Sequence[int]) -> bytes:
    encoded = json.dumps(
        list(token_ids),
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")
    if len(encoded) > MAX_CANONICAL_BYTES:
        raise ValueError("token_id_evidence_exceeds_byte_limit")
    return encoded


def encode_token_ids(token_ids: Sequence[int]) -> dict[str, Any]:
    """Encode the exact sequence while retaining independently checked facts."""

    normalised = _normalise_token_ids(token_ids)
    canonical = _canonical_bytes(normalised)
    return {
        "schema_version": TOKEN_EVIDENCE_SCHEMA_VERSION,
        "encoding": TOKEN_EVIDENCE_ENCODING,
        "token_count": len(normalised),
        "token_ids_sha256": hashlib.sha256(canonical).hexdigest(),
        "data": base64.b64encode(zlib.compress(canonical, level=9)).decode("ascii"),
    }


def decode_token_ids(evidence: Mapping[str, Any]) -> list[int]:
    """Decode and fail closed on metadata, compression, or canonicality drift."""

    if evidence.get("schema_version") != TOKEN_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("token_evidence_schema_version_mismatch")
    if evidence.get("encoding") != TOKEN_EVIDENCE_ENCODING:
        raise ValueError("token_evidence_encoding_mismatch")
    data = evidence.get("data")
    if not isinstance(data, str):
        raise ValueError("token_evidence_data_missing")
    try:
        compressed = base64.b64decode(data, validate=True)
        decompressor = zlib.decompressobj()
        canonical = decompressor.decompress(compressed, MAX_CANONICAL_BYTES + 1)
        canonical += decompressor.flush()
    except (ValueError, zlib.error) as exc:
        raise ValueError("token_evidence_decode_failed") from exc
    if (
        len(canonical) > MAX_CANONICAL_BYTES
        or decompressor.unconsumed_tail
        or decompressor.unused_data
    ):
        raise ValueError("token_evidence_decompressed_size_invalid")
    try:
        value = json.loads(canonical.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("token_evidence_json_invalid") from exc
    if not isinstance(value, list):
        raise ValueError("token_evidence_json_root_is_not_array")
    token_ids = _normalise_token_ids(value)
    if _canonical_bytes(token_ids) != canonical:
        raise ValueError("token_evidence_is_not_canonical")
    if evidence.get("token_count") != len(token_ids):
        raise ValueError("token_evidence_count_mismatch")
    actual_sha256 = hashlib.sha256(canonical).hexdigest()
    if evidence.get("token_ids_sha256") != actual_sha256:
        raise ValueError("token_evidence_hash_mismatch")
    return token_ids
