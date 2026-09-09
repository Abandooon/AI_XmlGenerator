from __future__ import annotations

import unittest

from neo4j_experiment_context import (
    DEFAULT_CONTEXT_BATCH_SIZE,
    _canonical_rows,
    _streaming_canonical_query_hash,
    canonical_sha256,
    collect_neo4j_context,
    verify_neo4j_context,
)


class _Result:
    def __init__(self, *, rows=None, single=None):
        self._rows = rows or []
        self._single = single

    def consume(self):
        return self

    def data(self):
        return list(self._rows)

    def single(self):
        return self._single


class _Session:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def run(self, query, **_parameters):
        if "RETURN 1 AS ok" in query:
            return _Result()
        if "CALL dbms.components()" in query:
            return _Result(rows=[{
                "name": "Neo4j Kernel",
                "versions": ["test-version"],
                "edition": "community",
            }])
        if "ConstraintDatasetV2" in query:
            return _Result(single={"status": "ready", "card_count": 2})
        if "labels(n) AS labels" in query:
            return _Result(rows=[
                {"labels": ["Class"], "properties": {"xml_tag": "B"}},
                {"properties": {"xml_tag": "A"}, "labels": ["Class"]},
            ])
        if "source_labels" in query:
            return _Result(rows=[{
                "source_labels": ["Class"],
                "source_properties": {"xml_tag": "A"},
                "relationship_type": "SUBCLASS_OF",
                "relationship_properties": {},
                "target_labels": ["Class"],
                "target_properties": {"xml_tag": "B"},
            }])
        if "constraint.constraint_id" in query:
            return _Result(rows=[{
                "constraint_id": "C1",
                "relationship_type": "APPLIES_TO_CLASS",
                "relationship_properties": {},
                "target_labels": ["Class"],
                "target_properties": {"xml_tag": "A"},
            }])
        if "collect(DISTINCT class.xml_tag)" in query:
            return _Result(single={"found": [
                "SENDER-RECEIVER-INTERFACE",
                "APPLICATION-SW-COMPONENT-TYPE",
            ]})
        raise AssertionError(query)


class _Driver:
    def session(self, *, database=None):
        self.database = database
        return _Session()


class Neo4jExperimentContextTests(unittest.TestCase):
    def test_streaming_hash_matches_in_memory_canonical_hash(self):
        rows = [
            {"b": 2, "a": "二"},
            {"a": "一", "b": 1},
        ]

        class Session:
            def run(self, _query, **_parameters):
                return _Result(rows=rows)

        count, digest = _streaming_canonical_query_hash(
            Session(), "RETURN rows", parameters={}
        )
        self.assertEqual(2, count)
        self.assertEqual(canonical_sha256(_canonical_rows(rows)), digest)

    def test_streaming_hash_uses_bounded_default_bolt_page(self):
        observed_batch_sizes = []

        class Session:
            def run(self, _query, **parameters):
                observed_batch_sizes.append(parameters["batch_size"])
                return _Result(rows=[])

        count, _digest = _streaming_canonical_query_hash(
            Session(), "RETURN rows", parameters={}
        )
        self.assertEqual(0, count)
        self.assertEqual([DEFAULT_CONTEXT_BATCH_SIZE], observed_batch_sizes)
        self.assertLessEqual(DEFAULT_CONTEXT_BATCH_SIZE, 25)

    def test_collect_is_credential_free_and_canonical(self):
        driver = _Driver()
        observed = collect_neo4j_context(
            driver,
            database="neo4j",
            dataset_sha256="a" * 64,
            expected_card_count=2,
        )
        self.assertEqual("neo4j", driver.database)
        self.assertEqual(2, observed["schema_node_count"])
        self.assertEqual(1, observed["schema_relationship_count"])
        self.assertEqual(1, observed["constraint_link_count"])
        self.assertEqual("Neo4j Kernel", observed["server_components"][0]["name"])
        self.assertFalse(observed["credentials_included"])
        unsigned = {
            key: value for key, value in observed.items()
            if key != "context_sha256"
        }
        self.assertEqual(canonical_sha256(unsigned), observed["context_sha256"])

    def test_verify_rejects_any_context_change(self):
        expected = {"context_sha256": "a", "schema_node_count": 1}
        verify_neo4j_context(dict(expected), expected)
        with self.assertRaisesRegex(RuntimeError, "schema_node_count"):
            verify_neo4j_context(
                {"context_sha256": "a", "schema_node_count": 2}, expected
            )


if __name__ == "__main__":
    unittest.main()
