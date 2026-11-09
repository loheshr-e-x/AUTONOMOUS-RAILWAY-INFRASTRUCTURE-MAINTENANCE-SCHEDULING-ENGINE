import unittest
from unittest import mock

from backend.app import logic_engine
from backend.app.logic_engine import verify_safety_invariants
from backend.app.schemas.contracts import (
    Department,
    ScheduledBlockAssignment,
    TimetableCoverage,
    TrackLine,
    TrainOccupancyWindow,
)


TRUSTED_SOURCE = "test-trusted-source"


class _FixtureProvider(logic_engine.EvidenceProvider):
    def authenticates_coverage(self, record):
        return record.source == TRUSTED_SOURCE

    def authenticates_isolation(self, assignment):
        return assignment.power_isolation_source == TRUSTED_SOURCE


def make_assignment(**updates):
    values = {
        "work_id": "W-1",
        "department": Department.ENGINEERING,
        "section_id": "NDLS_CNB",
        "start_time_hr": 10.0,
        "end_time_hr": 11.0,
        "worksite_start_km": 10.0,
        "worksite_end_km": 10.1,
    }
    values.update(updates)
    return ScheduledBlockAssignment(**values)


def make_train(**updates):
    values = {
        "train_no": "T-1",
        "section_id": "NDLS_CNB",
        "start_time_hr": 10.0,
        "end_time_hr": 11.0,
        "train_start_km": 11.1,
        "train_end_km": 11.2,
    }
    values.update(updates)
    return TrainOccupancyWindow(**values)


def make_coverage(**updates):
    values = {
        "source": TRUSTED_SOURCE,
        "section_id": "NDLS_CNB",
        "track_line": TrackLine.DOWN_LINE,
        "start_time_hr": 0.0,
        "end_time_hr": 24.0,
    }
    values.update(updates)
    return TimetableCoverage(**values)


class SafetyInvariantTests(unittest.TestCase):
    def setUp(self):
        # The application has no authenticating provider; tests install a fixture
        # one to exercise pass paths. It is test-only and not part of the app.
        patcher = mock.patch.object(
            logic_engine, "DEFAULT_EVIDENCE_PROVIDER", _FixtureProvider()
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def get_audit(self, audit, rule_name):
        return next(entry for entry in audit if entry.rule_name == rule_name)

    def test_clearance_rejects_overlapping_occupancy(self):
        valid, audit = verify_safety_invariants(
            [make_assignment()], [make_train()]
        )

        self.assertFalse(valid)
        self.assertFalse(
            self.get_audit(audit, "Passenger Train Clearance Invariant").passed
        )

    def test_adjacent_time_windows_do_not_overlap(self):
        valid, audit = verify_safety_invariants(
            [make_assignment(start_time_hr=9.0, end_time_hr=10.0)],
            [make_train(start_time_hr=10.0)],
            [make_coverage()],
        )

        self.assertTrue(valid)
        self.assertTrue(
            self.get_audit(audit, "Minimum Distance Safety Buffer").passed
        )

    def test_exact_standard_buffer_passes_and_short_buffer_fails(self):
        _, exact_audit = verify_safety_invariants(
            [make_assignment()],
            [make_train(train_start_km=11.1, train_end_km=11.2)],
        )
        _, short_audit = verify_safety_invariants(
            [make_assignment()],
            [make_train(train_start_km=11.0, train_end_km=11.1)],
        )

        self.assertTrue(
            self.get_audit(exact_audit, "Minimum Distance Safety Buffer").passed
        )
        self.assertFalse(
            self.get_audit(short_audit, "Minimum Distance Safety Buffer").passed
        )

    def test_traction_work_requires_isolation_and_uses_enhanced_buffer(self):
        unisolated, isolation_audit = verify_safety_invariants(
            [make_assignment(department=Department.TRACTION)],
            [make_train(train_start_km=12.1, train_end_km=12.2)],
        )
        isolated, isolated_audit = verify_safety_invariants(
            [
                make_assignment(
                    department=Department.TRACTION,
                    power_isolated=True,
                    power_isolation_source=TRUSTED_SOURCE,
                )
            ],
            [make_train(train_start_km=12.1, train_end_km=12.2)],
        )

        self.assertFalse(unisolated)
        missing_isolation = self.get_audit(
            isolation_audit, "Traction Power Isolation Rule"
        )
        self.assertIsNone(missing_isolation.passed)
        self.assertIn("unevaluated", missing_isolation.explanation)
        self.assertTrue(
            self.get_audit(isolated_audit, "Minimum Distance Safety Buffer").passed
        )
        self.assertFalse(isolated)

    def test_explicit_traction_isolation_evidence_passes(self):
        valid, audit = verify_safety_invariants(
            [
                make_assignment(
                    department=Department.TRACTION,
                    power_isolated=True,
                    power_isolation_source=TRUSTED_SOURCE,
                )
            ],
            [make_train(start_time_hr=11.0, end_time_hr=12.0)],
            [make_coverage()],
        )

        isolation = self.get_audit(audit, "Traction Power Isolation Rule")
        self.assertTrue(isolation.passed)
        self.assertIn("confirms", isolation.explanation)
        self.assertTrue(valid)

    def test_explicit_traction_isolation_failure_fails(self):
        valid, audit = verify_safety_invariants(
            [make_assignment(department=Department.TRACTION, power_isolated=False)],
            [],
        )

        isolation = self.get_audit(audit, "Traction Power Isolation Rule")
        self.assertFalse(isolation.passed)
        self.assertIn("not power-isolated", isolation.explanation)
        self.assertFalse(valid)

    def test_non_traction_isolation_rule_is_not_applicable(self):
        valid, audit = verify_safety_invariants(
            [make_assignment(power_isolated=None)],
            [make_train(start_time_hr=11.0, end_time_hr=12.0)],
            [make_coverage()],
        )

        isolation = self.get_audit(audit, "Traction Power Isolation Rule")
        self.assertTrue(isolation.passed)
        self.assertIn("does not apply", isolation.explanation)
        self.assertIsNone(make_assignment().power_isolated)
        self.assertTrue(valid)

    def test_heavy_equipment_requires_two_kilometers(self):
        _, exact_audit = verify_safety_invariants(
            [make_assignment(heavy_equipment=True)],
            [make_train(train_start_km=12.1, train_end_km=12.2)],
        )
        _, short_audit = verify_safety_invariants(
            [make_assignment(heavy_equipment=True)],
            [make_train(train_start_km=11.9, train_end_km=12.0)],
        )

        self.assertTrue(
            self.get_audit(exact_audit, "Minimum Distance Safety Buffer").passed
        )
        self.assertFalse(
            self.get_audit(short_audit, "Minimum Distance Safety Buffer").passed
        )

    def test_missing_spatial_evidence_fails_closed(self):
        valid, audit = verify_safety_invariants(
            [make_assignment(worksite_start_km=None, worksite_end_km=None)],
            [make_train(train_start_km=None, train_end_km=None)],
        )

        self.assertFalse(valid)
        self.assertFalse(
            self.get_audit(audit, "Minimum Distance Safety Buffer").passed
        )

    def test_different_sections_do_not_conflict(self):
        valid, audit = verify_safety_invariants(
            [make_assignment()],
            [make_train(section_id="NDLS_AGC")],
        )

        self.assertFalse(valid)
        self.assertIsNone(
            self.get_audit(audit, "Passenger Train Clearance Invariant").passed
        )

    def test_missing_train_windows_are_unverified(self):
        valid, audit = verify_safety_invariants([make_assignment()], [])

        self.assertFalse(valid)
        self.assertIsNone(
            self.get_audit(audit, "Passenger Train Clearance Invariant").passed
        )
        self.assertIsNone(
            self.get_audit(audit, "Minimum Distance Safety Buffer").passed
        )

    def test_clearance_is_evaluated_only_on_matching_track_line(self):
        valid, _ = verify_safety_invariants(
            [make_assignment(track_line=TrackLine.UP_LINE)],
            [make_train(track_line=TrackLine.DOWN_LINE)],
            [make_coverage(track_line=TrackLine.UP_LINE)],
        )
        self.assertTrue(valid)

        valid, _ = verify_safety_invariants(
            [make_assignment(track_line=TrackLine.UP_LINE)],
            [make_train(track_line=TrackLine.UP_LINE)],
        )
        self.assertFalse(valid)

    def test_heavy_equipment_on_up_line_needs_adjacent_down_line_buffer(self):
        heavy = make_assignment(track_line=TrackLine.UP_LINE, heavy_equipment=True)
        near = make_train(
            track_line=TrackLine.DOWN_LINE, train_start_km=10.5, train_end_km=10.6
        )
        valid, audit = verify_safety_invariants([heavy], [near])
        self.assertFalse(valid)
        self.assertFalse(
            self.get_audit(audit, "Adjacent Track Heavy Equipment Buffer").passed
        )

        far = make_train(
            track_line=TrackLine.DOWN_LINE, train_start_km=20.0, train_end_km=20.1
        )
        valid, audit = verify_safety_invariants(
            [heavy],
            [far],
            [
                make_coverage(track_line=TrackLine.UP_LINE),
                make_coverage(track_line=TrackLine.DOWN_LINE),
            ],
        )
        self.assertTrue(valid)
        self.assertTrue(
            self.get_audit(audit, "Adjacent Track Heavy Equipment Buffer").passed
        )

    def test_adjacent_rule_requires_down_line_coverage(self):
        heavy = make_assignment(track_line=TrackLine.UP_LINE, heavy_equipment=True)
        far = make_train(
            track_line=TrackLine.DOWN_LINE, train_start_km=20.0, train_end_km=20.1
        )
        up_cov = make_coverage(track_line=TrackLine.UP_LINE)
        down_cov = make_coverage(track_line=TrackLine.DOWN_LINE)
        rule = "Adjacent Track Heavy Equipment Buffer"
        cases = {
            "no trains, no coverage": ([], None, None),
            "no trains, UP only": ([], [up_cov], None),
            "listed far train, UP only": ([far], [up_cov], None),
            "wrong section": ([], [make_coverage(section_id="OTHER")], None),
            "partial start": ([], [make_coverage(start_time_hr=10.5)], None),
            "partial end": ([], [make_coverage(end_time_hr=10.5)], None),
            "no trains, DOWN coverage": ([], [up_cov, down_cov], True),
            "far train, DOWN coverage": ([far], [up_cov, down_cov], True),
        }
        for name, (trains, coverage, expected) in cases.items():
            with self.subTest(name):
                _, audit = verify_safety_invariants([heavy], trains, coverage)
                self.assertIs(self.get_audit(audit, rule).passed, expected)

    def test_adjacent_violation_fails_despite_valid_coverage(self):
        heavy = make_assignment(track_line=TrackLine.UP_LINE, heavy_equipment=True)
        near = make_train(
            track_line=TrackLine.DOWN_LINE, train_start_km=10.5, train_end_km=10.6
        )
        valid, audit = verify_safety_invariants(
            [heavy],
            [near],
            [
                make_coverage(track_line=TrackLine.UP_LINE),
                make_coverage(track_line=TrackLine.DOWN_LINE),
            ],
        )
        self.assertFalse(valid)
        self.assertIs(
            self.get_audit(audit, "Adjacent Track Heavy Equipment Buffer").passed,
            False,
        )

    def test_light_equipment_ignores_adjacent_line(self):
        valid, audit = verify_safety_invariants(
            [make_assignment(track_line=TrackLine.UP_LINE)],
            [make_train(track_line=TrackLine.DOWN_LINE)],
            [make_coverage(track_line=TrackLine.UP_LINE)],
        )
        self.assertTrue(valid)
        self.assertFalse(
            any(e.rule_name == "Adjacent Track Heavy Equipment Buffer" for e in audit)
        )

    def test_confirmed_complete_timetable_establishes_no_conflicting_train(self):
        valid, audit = verify_safety_invariants(
            [make_assignment()], [], [make_coverage()]
        )

        self.assertTrue(valid)
        self.assertTrue(
            self.get_audit(audit, "Passenger Train Clearance Invariant").passed
        )
        self.assertTrue(
            self.get_audit(audit, "Minimum Distance Safety Buffer").passed
        )

    def test_incomplete_timetable_coverage_is_unverified(self):
        for coverage in (
            make_coverage(track_line=TrackLine.UP_LINE),
            make_coverage(section_id="OTHER"),
            make_coverage(start_time_hr=10.5),
            make_coverage(end_time_hr=10.5),
        ):
            with self.subTest(coverage=coverage):
                valid, audit = verify_safety_invariants(
                    [make_assignment()], [], [coverage]
                )
                self.assertFalse(valid)
                self.assertIsNone(
                    self.get_audit(audit, "Passenger Train Clearance Invariant").passed
                )

    def test_other_track_trains_alone_do_not_establish_clearance(self):
        valid, audit = verify_safety_invariants(
            [make_assignment()],
            [make_train(track_line=TrackLine.UP_LINE)],
        )

        self.assertFalse(valid)
        self.assertIsNone(
            self.get_audit(audit, "Passenger Train Clearance Invariant").passed
        )

    def test_non_overlapping_listed_train_without_coverage_is_unverified(self):
        valid, audit = verify_safety_invariants(
            [make_assignment()],
            [make_train(start_time_hr=12.0, end_time_hr=13.0)],
        )

        self.assertFalse(valid)
        clearance = self.get_audit(audit, "Passenger Train Clearance Invariant")
        self.assertIsNone(clearance.passed)
        self.assertIn("completeness", clearance.explanation)
        buffers = [e for e in audit if e.rule_name == "Minimum Distance Safety Buffer"]
        self.assertTrue(any(e.passed is True for e in buffers))
        unknown = [e for e in buffers if e.passed is None]
        self.assertEqual(len(unknown), 1)
        self.assertIn("unlisted trains is unknown", unknown[0].explanation)

    def test_non_overlapping_listed_train_with_coverage_passes(self):
        valid, audit = verify_safety_invariants(
            [make_assignment()],
            [make_train(start_time_hr=12.0, end_time_hr=13.0)],
            [make_coverage()],
        )

        self.assertTrue(valid)
        self.assertTrue(
            all(e.passed is True for e in audit if "Clearance" in e.rule_name
                or "Buffer" in e.rule_name)
        )

    def test_conflicting_listed_train_fails_even_with_coverage(self):
        valid, audit = verify_safety_invariants(
            [make_assignment()],
            [make_train(train_start_km=10.3, train_end_km=10.4)],
            [make_coverage()],
        )

        self.assertFalse(valid)
        self.assertFalse(
            self.get_audit(audit, "Passenger Train Clearance Invariant").passed
        )
        self.assertFalse(
            self.get_audit(audit, "Minimum Distance Safety Buffer").passed
        )

    def test_bad_coverage_with_listed_train_stays_unevaluated(self):
        train = make_train(start_time_hr=12.0, end_time_hr=13.0)
        for coverage in (
            make_coverage(track_line=TrackLine.UP_LINE),
            make_coverage(section_id="OTHER"),
            make_coverage(start_time_hr=10.5),
            make_coverage(end_time_hr=10.5),
        ):
            with self.subTest(coverage=coverage):
                valid, audit = verify_safety_invariants(
                    [make_assignment()], [train], [coverage]
                )
                self.assertFalse(valid)
                self.assertIsNone(
                    self.get_audit(audit, "Passenger Train Clearance Invariant").passed
                )
        valid, _ = verify_safety_invariants([make_assignment()], [train])
        self.assertFalse(valid)

    ADJACENT_RULE = "Adjacent Track Heavy Equipment Buffer"
    DIRECTIONS = (
        (TrackLine.UP_LINE, TrackLine.DOWN_LINE),
        (TrackLine.DOWN_LINE, TrackLine.UP_LINE),
    )

    def _adjacent_status(self, own, trains, coverage, **work):
        heavy = make_assignment(track_line=own, heavy_equipment=True, **work)
        valid, audit = verify_safety_invariants([heavy], trains, coverage)
        return valid, self.get_audit(audit, self.ADJACENT_RULE).passed

    def test_adjacent_rule_known_violation_fails_in_both_directions(self):
        for own, adj in self.DIRECTIONS:
            near = make_train(
                track_line=adj, train_start_km=10.5, train_end_km=10.6
            )
            for coverage in (None, [make_coverage(track_line=adj)]):
                with self.subTest(own=own, covered=coverage is not None):
                    valid, passed = self._adjacent_status(own, [near], coverage)
                    self.assertFalse(valid)
                    self.assertIs(passed, False)

    def test_adjacent_rule_without_trains_or_coverage_is_unevaluated(self):
        for own, _ in self.DIRECTIONS:
            with self.subTest(own=own):
                valid, passed = self._adjacent_status(own, [], None)
                self.assertFalse(valid)
                self.assertIsNone(passed)

    def test_adjacent_rule_passes_only_with_adjacent_line_coverage(self):
        for own, adj in self.DIRECTIONS:
            far = make_train(track_line=adj, train_start_km=20.0, train_end_km=20.1)
            for trains in ([], [far]):
                with self.subTest(own=own, trains=len(trains)):
                    _, passed = self._adjacent_status(
                        own, trains, [make_coverage(track_line=adj)]
                    )
                    self.assertIs(passed, True)

    def test_adjacent_rule_own_line_coverage_is_not_enough(self):
        for own, _ in self.DIRECTIONS:
            with self.subTest(own=own):
                _, passed = self._adjacent_status(
                    own, [], [make_coverage(track_line=own)]
                )
                self.assertIsNone(passed)

    def test_adjacent_rule_incomplete_or_mismatched_coverage_is_unevaluated(self):
        for own, adj in self.DIRECTIONS:
            for label, coverage in (
                ("wrong section", make_coverage(track_line=adj, section_id="OTHER")),
                ("partial start", make_coverage(track_line=adj, start_time_hr=10.5)),
                ("partial end", make_coverage(track_line=adj, end_time_hr=10.5)),
            ):
                with self.subTest(own=own, case=label):
                    _, passed = self._adjacent_status(own, [], [coverage])
                    self.assertIsNone(passed)

    def test_adjacent_rule_missing_spatial_data_never_passes(self):
        for own, adj in self.DIRECTIONS:
            train = make_train(
                track_line=adj, train_start_km=None, train_end_km=None
            )
            with self.subTest(own=own):
                _, passed = self._adjacent_status(
                    own, [train], [make_coverage(track_line=adj)]
                )
                self.assertIs(passed, False)

    def test_adjacent_rule_inverted_spatial_interval_never_passes(self):
        for own, adj in self.DIRECTIONS:
            train = make_train(
                track_line=adj, train_start_km=20.1, train_end_km=20.0
            )
            with self.subTest(own=own):
                _, passed = self._adjacent_status(
                    own, [train], [make_coverage(track_line=adj)]
                )
                self.assertIs(passed, False)

    def test_adjacent_rule_invalid_train_interval_is_unevaluated(self):
        for own, adj in self.DIRECTIONS:
            train = make_train(
                track_line=adj, start_time_hr=11.0, end_time_hr=10.0
            )
            with self.subTest(own=own):
                _, passed = self._adjacent_status(
                    own, [train], [make_coverage(track_line=adj)]
                )
                self.assertIsNone(passed)

    def test_non_heavy_work_has_no_adjacent_rule_entry(self):
        for own, adj in self.DIRECTIONS:
            _, audit = verify_safety_invariants(
                [make_assignment(track_line=own)],
                [make_train(track_line=adj)],
                [make_coverage(track_line=own)],
            )
            self.assertFalse(any(e.rule_name == self.ADJACENT_RULE for e in audit))


    def test_empty_schedule_is_never_verified(self):
        for trains in ([], [make_train()]):
            with self.subTest(trains=len(trains)):
                valid, audit = verify_safety_invariants([], trains, [make_coverage()])
                self.assertFalse(valid)
                self.assertEqual(audit, [])

    def test_non_empty_schedule_without_evidence_stays_unverified(self):
        valid, audit = verify_safety_invariants([make_assignment()], [])
        self.assertFalse(valid)
        self.assertTrue(audit)
        self.assertTrue(any(e.passed is None for e in audit))


    def test_coverage_without_trusted_source_does_not_establish_completeness(self):
        for source in (None, "", "unknown-caller"):
            for own in (TrackLine.DOWN_LINE, TrackLine.UP_LINE):
                with self.subTest(source=source, own=own):
                    adj = (
                        TrackLine.UP_LINE
                        if own == TrackLine.DOWN_LINE
                        else TrackLine.DOWN_LINE
                    )
                    coverage = [
                        make_coverage(source=source, track_line=own),
                        make_coverage(source=source, track_line=adj),
                    ]
                    valid, audit = verify_safety_invariants(
                        [make_assignment(track_line=own, heavy_equipment=True)],
                        [],
                        coverage,
                    )
                    self.assertFalse(valid)
                    self.assertIsNone(
                        self.get_audit(audit, "Passenger Train Clearance Invariant").passed
                    )
                    self.assertIsNone(self.get_audit(audit, self.ADJACENT_RULE).passed)

    def test_bare_positive_isolation_boolean_is_unevaluated(self):
        for source in (None, "", "unknown-caller"):
            with self.subTest(source=source):
                valid, audit = verify_safety_invariants(
                    [
                        make_assignment(
                            department=Department.TRACTION,
                            power_isolated=True,
                            power_isolation_source=source,
                        )
                    ],
                    [],
                    [make_coverage()],
                )
                isolation = self.get_audit(audit, "Traction Power Isolation Rule")
                self.assertIsNone(isolation.passed)
                self.assertIn("provenance", isolation.explanation)
                self.assertFalse(valid)

    def test_explicit_negative_isolation_fails_regardless_of_source(self):
        for source in (None, TRUSTED_SOURCE):
            with self.subTest(source=source):
                _, audit = verify_safety_invariants(
                    [
                        make_assignment(
                            department=Department.TRACTION,
                            power_isolated=False,
                            power_isolation_source=source,
                        )
                    ],
                    [],
                )
                self.assertIs(
                    self.get_audit(audit, "Traction Power Isolation Rule").passed, False
                )

    def test_non_traction_work_ignores_isolation_evidence_and_source(self):
        _, audit = verify_safety_invariants(
            [make_assignment(power_isolated=True, power_isolation_source=None)],
            [],
            [make_coverage()],
        )
        isolation = self.get_audit(audit, "Traction Power Isolation Rule")
        self.assertIs(isolation.passed, True)
        self.assertIn("does not apply", isolation.explanation)


    def test_base_provider_authenticates_nothing_even_for_well_formed_evidence(self):
        provider = logic_engine.EvidenceProvider()
        traction = make_assignment(
            department=Department.TRACTION,
            power_isolated=True,
            power_isolation_source=TRUSTED_SOURCE,
        )
        valid, audit = verify_safety_invariants(
            [traction],
            [],
            [make_coverage(), make_coverage(track_line=TrackLine.UP_LINE)],
            evidence_provider=provider,
        )

        self.assertFalse(valid)
        self.assertIsNone(self.get_audit(audit, "Traction Power Isolation Rule").passed)
        self.assertIsNone(
            self.get_audit(audit, "Passenger Train Clearance Invariant").passed
        )

    def test_provider_cannot_turn_a_known_violation_into_a_pass(self):
        valid, audit = verify_safety_invariants(
            [make_assignment()],
            [make_train()],
            [make_coverage()],
            evidence_provider=_FixtureProvider(),
        )

        self.assertFalse(valid)
        self.assertIs(
            self.get_audit(audit, "Passenger Train Clearance Invariant").passed, False
        )

    def test_provider_authentication_is_per_record_not_per_label(self):
        class OnlyDownLine(logic_engine.EvidenceProvider):
            def authenticates_coverage(self, record):
                return record.track_line == TrackLine.DOWN_LINE

        forged = make_coverage(track_line=TrackLine.UP_LINE, source=TRUSTED_SOURCE)
        _, audit = verify_safety_invariants(
            [make_assignment(track_line=TrackLine.UP_LINE)],
            [],
            [forged],
            evidence_provider=OnlyDownLine(),
        )

        self.assertIsNone(
            self.get_audit(audit, "Passenger Train Clearance Invariant").passed
        )


if __name__ == "__main__":
    unittest.main()
