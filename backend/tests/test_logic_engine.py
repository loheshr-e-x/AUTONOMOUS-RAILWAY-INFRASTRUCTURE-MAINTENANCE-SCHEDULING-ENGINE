import unittest

from backend.app.logic_engine import verify_safety_invariants
from backend.app.schemas.contracts import (
    Department,
    ScheduledBlockAssignment,
    TrackLine,
    TrainOccupancyWindow,
)


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


class SafetyInvariantTests(unittest.TestCase):
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
                    department=Department.TRACTION, power_isolated=True
                )
            ],
            [make_train(train_start_km=12.1, train_end_km=12.2)],
        )

        self.assertFalse(unisolated)
        self.assertFalse(
            self.get_audit(isolation_audit, "Traction Power Isolation Rule").passed
        )
        self.assertTrue(
            self.get_audit(isolated_audit, "Minimum Distance Safety Buffer").passed
        )
        self.assertFalse(isolated)

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

        self.assertTrue(valid)
        self.assertTrue(
            self.get_audit(audit, "Passenger Train Clearance Invariant").passed
        )

    def test_clearance_is_evaluated_only_on_matching_track_line(self):
        valid, _ = verify_safety_invariants(
            [make_assignment(track_line=TrackLine.UP_LINE)],
            [make_train(track_line=TrackLine.DOWN_LINE)],
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
        valid, audit = verify_safety_invariants([heavy], [far])
        self.assertTrue(valid)
        self.assertTrue(
            self.get_audit(audit, "Adjacent Track Heavy Equipment Buffer").passed
        )

    def test_light_equipment_ignores_adjacent_line(self):
        valid, audit = verify_safety_invariants(
            [make_assignment(track_line=TrackLine.UP_LINE)],
            [make_train(track_line=TrackLine.DOWN_LINE)],
        )
        self.assertTrue(valid)
        self.assertFalse(
            any(e.rule_name == "Adjacent Track Heavy Equipment Buffer" for e in audit)
        )


if __name__ == "__main__":
    unittest.main()
