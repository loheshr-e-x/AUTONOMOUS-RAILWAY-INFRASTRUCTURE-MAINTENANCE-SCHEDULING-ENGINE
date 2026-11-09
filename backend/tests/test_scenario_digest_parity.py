from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from backend.app.scenario_validation import canonical_scenario_digest
from backend.app.schemas.scenario_contracts import ScenarioComparisonRequest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "task16-canonical-digest.json"
JAVASCRIPT_DIGEST_RUNNER = (
    REPOSITORY_ROOT / "frontend" / "tests" / "scenario-digest-cli.mjs"
)


def _set_path(target: dict[str, Any], path: list[str | int], value: Any) -> None:
    current: Any = target
    for part in path[:-1]:
        current = current[part]
    current[path[-1]] = value


def _reversed_object_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _reversed_object_keys(item)
            for key, item in reversed(list(value.items()))
        }
    if isinstance(value, list):
        return [_reversed_object_keys(item) for item in value]
    return value


def _digest_requests(fixtures: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    baseline = fixtures["baseline"]
    named_requests = [
        (case["name"], copy.deepcopy(case["request"]))
        for case in fixtures["cases"]
    ]
    named_requests.extend(
        [
            ("explicit defaults", copy.deepcopy(fixtures["default_equivalent_request"])),
            ("reordered object keys", _reversed_object_keys(baseline)),
        ]
    )

    metadata_only = copy.deepcopy(baseline)
    metadata_only.update(fixtures["irrelevant_metadata"])
    named_requests.append(("irrelevant metadata changed", metadata_only))

    for mutation in fixtures["digest_mutations"]:
        changed = copy.deepcopy(baseline)
        if mutation["value"] == "reverse":
            current: Any = changed
            for part in mutation["path"][:-1]:
                current = current[part]
            current[mutation["path"][-1]] = list(reversed(current[mutation["path"][-1]]))
        else:
            _set_path(changed, mutation["path"], mutation["value"])
        named_requests.append((f"mutation: {mutation['name']}", changed))

    return [request for _, request in named_requests], [name for name, _ in named_requests]


def _python_digests(requests: list[dict[str, Any]]) -> list[str]:
    return [
        canonical_scenario_digest(ScenarioComparisonRequest.model_validate(request))
        for request in requests
    ]


def test_python_and_javascript_canonical_digests_match_shared_fixtures() -> None:
    node = shutil.which("node")
    assert node is not None, "Node.js is required for the cross-language digest parity test."
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    requests, names = _digest_requests(fixtures)

    completed = subprocess.run(
        [node, "--experimental-strip-types", str(JAVASCRIPT_DIGEST_RUNNER)],
        cwd=REPOSITORY_ROOT,
        input=json.dumps({"requests": requests}, ensure_ascii=True),
        capture_output=True,
        check=True,
        text=True,
        timeout=30,
    )
    javascript_digests = json.loads(completed.stdout)["digests"]
    python_digests = _python_digests(requests)

    assert len(javascript_digests) == len(names)
    assert len(python_digests) == len(names)
    for name, python_digest, javascript_digest in zip(
        names, python_digests, javascript_digests, strict=True
    ):
        assert javascript_digest == python_digest, f"digest mismatch for {name}"


def test_every_digest_relevant_fixture_mutation_changes_python_digest() -> None:
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    baseline = copy.deepcopy(fixtures["baseline"])
    original_digest = canonical_scenario_digest(
        ScenarioComparisonRequest.model_validate(baseline)
    )

    for mutation in fixtures["digest_mutations"]:
        changed = copy.deepcopy(baseline)
        if mutation["value"] == "reverse":
            current: Any = changed
            for part in mutation["path"][:-1]:
                current = current[part]
            current[mutation["path"][-1]] = list(reversed(current[mutation["path"][-1]]))
        else:
            _set_path(changed, mutation["path"], mutation["value"])
        changed_digest = canonical_scenario_digest(
            ScenarioComparisonRequest.model_validate(changed)
        )
        assert changed_digest != original_digest, (
            f"digest did not change for {mutation['name']}"
        )


def test_python_digest_ignores_scenario_presentation_metadata() -> None:
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    baseline = copy.deepcopy(fixtures["baseline"])
    changed = copy.deepcopy(baseline)
    changed.update(fixtures["irrelevant_metadata"])

    assert canonical_scenario_digest(
        ScenarioComparisonRequest.model_validate(changed)
    ) == canonical_scenario_digest(ScenarioComparisonRequest.model_validate(baseline))


def test_python_digest_uses_contract_defaults_for_omitted_fields() -> None:
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    omitted = fixtures["cases"][2]["request"]
    explicit = fixtures["default_equivalent_request"]

    assert canonical_scenario_digest(
        ScenarioComparisonRequest.model_validate(omitted)
    ) == canonical_scenario_digest(ScenarioComparisonRequest.model_validate(explicit))
