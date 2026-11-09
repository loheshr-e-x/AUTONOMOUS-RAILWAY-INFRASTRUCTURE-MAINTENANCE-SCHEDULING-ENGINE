# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: audit.spec.ts >> B (cont.). Solver outcome communication >> B11 production UI communicates an unschedulable/partial outcome and lists unscheduled work orders
- Location: tests/audit.spec.ts:221:7

# Error details

```
Error: solver outcome shown

expect(received).toMatch(expected)

Expected pattern: /unschedulable/i
Received string:  "SymbIO-Block Dashboard·
Symbolic CSP & FOL railway maintenance block scheduling·
API online
Audit Log
171
Offline simulation scenarios·
Saved scenarios stay in this browser. Running a comparison sends the selected scenario to the experimental API; results are not saved. Do not enter credentials, evidence, or operational railway data. This prototype is not operationally authorized.·
Reload saved
Save scenarios
New scenario name
Scenario sections·
NDLS_CNB · New Delhi - Kanpur Central·
NDLS_CNB_SEC1
NDLS_CNB_SEC2
NDLS_CNB_SEC3·
HWH_PURI · Howrah - Puri·
HWH_PURI_SEC1
HWH_PURI_SEC2
HWH_PURI_SEC3·
BCT_AMD · Mumbai Central - Ahmedabad·
BCT_AMD_SEC1
BCT_AMD_SEC2
BCT_AMD_SEC3·
Section IDs come from the backend route list. Existing work orders and train windows must be moved explicitly if you remove their current section.·
Create·
No saved scenarios yet.·
Create an offline scenario above. It will remain a draft until saved.·
Scenario solver comparison·
Offline, non-operational simulation. This runs the selected browser-local scenario (including any unsaved edits) against the experimental API; it does not change saved scenario storage or assess railway safety.·
Run comparison·
Create or select a scenario above to compare it.·
Corridor
NDLS_CNB · New Delhi - Kanpur Central
HWH_PURI · Howrah - Puri
BCT_AMD · Mumbai Central - Ahmedabad
Section IDs (comma separated)
Horizon (hrs)
AC-3 pruning
Simulated annealing
Timetable
Work Orders
30
Generate Schedule
Search Space Pruned (AC-3)
92.0%
Safety Rule Compliance
—
Track Hours Saved
1.0 h
1 co-location merges
1 Parallel Maintenance Requests Bundled into Co-Located Block Windows
Solver Speed
1 ms
2/30 blocks scheduled
Time-Space Schedule · status: safety_unverified
00:00
NDLS_CNB_SEC1
UP LINE
SIG
WO-26027-019
ENG
WO-26027-021
DOWN LINE
12350
12418
12452
12582
14038
14620
22450
22582
NDLS_CNB_SEC2
UP LINE
12397
12565
DOWN LINE
12418
12554
12556
12562
12582
15566
20802
22582
NDLS_CNB_SEC3
UP LINE
12273
12281
12303
12381
12397
12417
12451
12553
12555
12565
15565
DOWN LINE
12260
12554
12560
12562
15566
22362
Train occupancy
ENG = ENGINEERING
SIG = SIGNALLING
TRC = TRACTION
Striped = co-located block
Work Order Inspection·
Click a maintenance block on the Gantt chart to inspect its work order.·
FOL Audit Log
All rules (171)
WO-26027-019 — NDLS_CNB_SEC1 UP LINE 0–1h
WO-26027-021 — NDLS_CNB_SEC1 UP LINE 0–1h
AC3DomainPruning
all_candidate_domains_nonempty_after_ac3·
AC-3 removed 1 of 3 candidate starts remaining after train-conflict filtering.·
Scheduled Block Time Validity
0 <= 0.0 < 1.0 <= 24·
Work WO-26027-019 has a valid scheduled time interval.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12003) and no_time_overlap(0.0, 1.0, 20.53030303030303, 22.416666666666668)·
No conflict with listed train 12003, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12003)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12033) and no_time_overlap(0.0, 1.0, 9.515151515151516, 11.333333333333334)·
No conflict with listed train 12033, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12033)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12259) and no_time_overlap(0.0, 1.0, 9.125, 11.0)·
No conflict with listed train 12259, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12259)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12273) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12273, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12273)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12281) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12281, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12281)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12301) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12301, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12301)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12303) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12303, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12303)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12305) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12305, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12305)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12309) and no_time_overlap(0.0, 1.0, 5.8484848484848495, 7.666666666666668)·
No conflict with listed train 12309, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12309)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12313) and no_time_overlap(0.0, 1.0, 8.958333333333334, 10.833333333333334)·
No conflict with listed train 12313, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12313)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12349) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 12349, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12349)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12381) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12381, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12381)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12393) and no_time_overlap(0.0, 1.0, 6.070075757575758, 7.916666666666667)·
No conflict with listed train 12393, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12393)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12397) and no_time_overlap(0.0, 1.0, 2.121212121212121, 4.166666666666668)·
No conflict with listed train 12397, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12397)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12417) and no_time_overlap(0.0, 1.0, 4.784090909090909, 7.0)·
No conflict with listed train 12417, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12417)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12419) and no_time_overlap(0.0, 1.0, 12.397727272727273, 15.0)·
No conflict with listed train 12419, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12419)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12423) and no_time_overlap(0.0, 1.0, 8.625, 10.5)·
No conflict with listed train 12423, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12423)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12451) and no_time_overlap(0.0, 1.0, 3.871212121212121, 5.916666666666668)·
No conflict with listed train 12451, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12451)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12453) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12453, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12453)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12553) and no_time_overlap(0.0, 1.0, 4.1439393939393945, 6.416666666666668)·
No conflict with listed train 12553, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12553)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12555) and no_time_overlap(0.0, 1.0, 3.25, 5.25)·
No conflict with listed train 12555, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12555)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12559) and no_time_overlap(0.0, 1.0, 6.568181818181818, 8.5)·
No conflict with listed train 12559, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12559)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12561) and no_time_overlap(0.0, 1.0, 13.676136363636363, 15.75)·
No conflict with listed train 12561, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12561)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12565) and no_time_overlap(0.0, 1.0, 2.924242424242422, 5.083333333333332)·
No conflict with listed train 12565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 12581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12877) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12877, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12877)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 13007) and no_time_overlap(0.0, 1.0, 15.916666666666668, 19.666666666666668)·
No conflict with listed train 13007, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,13007)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 14037) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 14037, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,14037)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 14619) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 14619, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,14619)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 15565) and no_time_overlap(0.0, 1.0, 4.198863636363637, 6.5)·
No conflict with listed train 15565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,15565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20407) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20407, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20407)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20801) and no_time_overlap(0.0, 1.0, 9.301136363636363, 12.0)·
No conflict with listed train 20801, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20801)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20817) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 20817, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20817)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20839) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20839, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20839)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22361) and no_time_overlap(0.0, 1.0, 10.212121212121211, 13.166666666666666)·
No conflict with listed train 22361, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22361)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22415) and no_time_overlap(0.0, 1.0, 12.520833333333334, 14.083333333333334)·
No conflict with listed train 22415, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22415)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22435) and no_time_overlap(0.0, 1.0, 21.477272727272727, 23.0)·
No conflict with listed train 22435, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22435)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22449) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 22449, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22449)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 22581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22811) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22811, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22811)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22823) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22823, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22823)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Minimum Distance Safety Buffer
timetable_complete_for_exposure(NDLS_CNB_SEC1, UP_LINE)·
Exposure to unlisted trains is unknown: no timetable completeness evidence covers this section, track line, and scheduled interval.·
Traction Power Isolation Rule
not_traction_work(WO-26027-019) or power_isolated(WO-26027-019)·
Work WO-26027-019 is not traction work; the traction isolation rule does not apply.·
Scheduled Block Time Validity
0 <= 0.0 < 1.0 <= 24·
Work WO-26027-021 has a valid scheduled time interval.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12003) and no_time_overlap(0.0, 1.0, 20.53030303030303, 22.416666666666668)·
No conflict with listed train 12003, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12003)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12033) and no_time_overlap(0.0, 1.0, 9.515151515151516, 11.333333333333334)·
No conflict with listed train 12033, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12033)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12259) and no_time_overlap(0.0, 1.0, 9.125, 11.0)·
No conflict with listed train 12259, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12259)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12273) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12273, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12273)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12281) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12281, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12281)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12301) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12301, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12301)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12303) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12303, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12303)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12305) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12305, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12305)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12309) and no_time_overlap(0.0, 1.0, 5.8484848484848495, 7.666666666666668)·
No conflict with listed train 12309, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12309)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12313) and no_time_overlap(0.0, 1.0, 8.958333333333334, 10.833333333333334)·
No conflict with listed train 12313, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12313)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12349) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 12349, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12349)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12381) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12381, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12381)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12393) and no_time_overlap(0.0, 1.0, 6.070075757575758, 7.916666666666667)·
No conflict with listed train 12393, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12393)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12397) and no_time_overlap(0.0, 1.0, 2.121212121212121, 4.166666666666668)·
No conflict with listed train 12397, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12397)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12417) and no_time_overlap(0.0, 1.0, 4.784090909090909, 7.0)·
No conflict with listed train 12417, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12417)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12419) and no_time_overlap(0.0, 1.0, 12.397727272727273, 15.0)·
No conflict with listed train 12419, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12419)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12423) and no_time_overlap(0.0, 1.0, 8.625, 10.5)·
No conflict with listed train 12423, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12423)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12451) and no_time_overlap(0.0, 1.0, 3.871212121212121, 5.916666666666668)·
No conflict with listed train 12451, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12451)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12453) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12453, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12453)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12553) and no_time_overlap(0.0, 1.0, 4.1439393939393945, 6.416666666666668)·
No conflict with listed train 12553, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12553)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12555) and no_time_overlap(0.0, 1.0, 3.25, 5.25)·
No conflict with listed train 12555, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12555)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12559) and no_time_overlap(0.0, 1.0, 6.568181818181818, 8.5)·
No conflict with listed train 12559, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12559)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12561) and no_time_overlap(0.0, 1.0, 13.676136363636363, 15.75)·
No conflict with listed train 12561, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12561)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12565) and no_time_overlap(0.0, 1.0, 2.924242424242422, 5.083333333333332)·
No conflict with listed train 12565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 12581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12877) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12877, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12877)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 13007) and no_time_overlap(0.0, 1.0, 15.916666666666668, 19.666666666666668)·
No conflict with listed train 13007, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,13007)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 14037) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 14037, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,14037)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 14619) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 14619, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,14619)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 15565) and no_time_overlap(0.0, 1.0, 4.198863636363637, 6.5)·
No conflict with listed train 15565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,15565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20407) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20407, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20407)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20801) and no_time_overlap(0.0, 1.0, 9.301136363636363, 12.0)·
No conflict with listed train 20801, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20801)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20817) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 20817, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20817)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20839) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20839, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20839)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22361) and no_time_overlap(0.0, 1.0, 10.212121212121211, 13.166666666666666)·
No conflict with listed train 22361, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22361)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22415) and no_time_overlap(0.0, 1.0, 12.520833333333334, 14.083333333333334)·
No conflict with listed train 22415, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22415)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22435) and no_time_overlap(0.0, 1.0, 21.477272727272727, 23.0)·
No conflict with listed train 22435, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22435)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22449) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 22449, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22449)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 22581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22811) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22811, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22811)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22823) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22823, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22823)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Minimum Distance Safety Buffer
timetable_complete_for_exposure(NDLS_CNB_SEC1, UP_LINE)·
Exposure to unlisted trains is unknown: no timetable completeness evidence covers this section, track line, and scheduled interval.·
Traction Power Isolation Rule
not_traction_work(WO-26027-021) or power_isolated(WO-26027-021)·
Work WO-26027-021 is not traction work; the traction isolation rule does not apply."
```

```
Error: unscheduled work-order IDs shown

expect(received).toContain(expected) // indexOf

Expected substring: "WO-26027-001"
Received string:    "SymbIO-Block Dashboard·
Symbolic CSP & FOL railway maintenance block scheduling·
API online
Audit Log
171
Offline simulation scenarios·
Saved scenarios stay in this browser. Running a comparison sends the selected scenario to the experimental API; results are not saved. Do not enter credentials, evidence, or operational railway data. This prototype is not operationally authorized.·
Reload saved
Save scenarios
New scenario name
Scenario sections·
NDLS_CNB · New Delhi - Kanpur Central·
NDLS_CNB_SEC1
NDLS_CNB_SEC2
NDLS_CNB_SEC3·
HWH_PURI · Howrah - Puri·
HWH_PURI_SEC1
HWH_PURI_SEC2
HWH_PURI_SEC3·
BCT_AMD · Mumbai Central - Ahmedabad·
BCT_AMD_SEC1
BCT_AMD_SEC2
BCT_AMD_SEC3·
Section IDs come from the backend route list. Existing work orders and train windows must be moved explicitly if you remove their current section.·
Create·
No saved scenarios yet.·
Create an offline scenario above. It will remain a draft until saved.·
Scenario solver comparison·
Offline, non-operational simulation. This runs the selected browser-local scenario (including any unsaved edits) against the experimental API; it does not change saved scenario storage or assess railway safety.·
Run comparison·
Create or select a scenario above to compare it.·
Corridor
NDLS_CNB · New Delhi - Kanpur Central
HWH_PURI · Howrah - Puri
BCT_AMD · Mumbai Central - Ahmedabad
Section IDs (comma separated)
Horizon (hrs)
AC-3 pruning
Simulated annealing
Timetable
Work Orders
30
Generate Schedule
Search Space Pruned (AC-3)
92.0%
Safety Rule Compliance
—
Track Hours Saved
1.0 h
1 co-location merges
1 Parallel Maintenance Requests Bundled into Co-Located Block Windows
Solver Speed
1 ms
2/30 blocks scheduled
Time-Space Schedule · status: safety_unverified
00:00
NDLS_CNB_SEC1
UP LINE
SIG
WO-26027-019
ENG
WO-26027-021
DOWN LINE
12350
12418
12452
12582
14038
14620
22450
22582
NDLS_CNB_SEC2
UP LINE
12397
12565
DOWN LINE
12418
12554
12556
12562
12582
15566
20802
22582
NDLS_CNB_SEC3
UP LINE
12273
12281
12303
12381
12397
12417
12451
12553
12555
12565
15565
DOWN LINE
12260
12554
12560
12562
15566
22362
Train occupancy
ENG = ENGINEERING
SIG = SIGNALLING
TRC = TRACTION
Striped = co-located block
Work Order Inspection·
Click a maintenance block on the Gantt chart to inspect its work order.·
FOL Audit Log
All rules (171)
WO-26027-019 — NDLS_CNB_SEC1 UP LINE 0–1h
WO-26027-021 — NDLS_CNB_SEC1 UP LINE 0–1h
AC3DomainPruning
all_candidate_domains_nonempty_after_ac3·
AC-3 removed 1 of 3 candidate starts remaining after train-conflict filtering.·
Scheduled Block Time Validity
0 <= 0.0 < 1.0 <= 24·
Work WO-26027-019 has a valid scheduled time interval.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12003) and no_time_overlap(0.0, 1.0, 20.53030303030303, 22.416666666666668)·
No conflict with listed train 12003, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12003)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12033) and no_time_overlap(0.0, 1.0, 9.515151515151516, 11.333333333333334)·
No conflict with listed train 12033, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12033)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12259) and no_time_overlap(0.0, 1.0, 9.125, 11.0)·
No conflict with listed train 12259, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12259)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12273) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12273, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12273)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12281) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12281, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12281)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12301) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12301, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12301)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12303) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12303, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12303)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12305) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12305, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12305)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12309) and no_time_overlap(0.0, 1.0, 5.8484848484848495, 7.666666666666668)·
No conflict with listed train 12309, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12309)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12313) and no_time_overlap(0.0, 1.0, 8.958333333333334, 10.833333333333334)·
No conflict with listed train 12313, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12313)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12349) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 12349, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12349)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12381) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12381, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12381)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12393) and no_time_overlap(0.0, 1.0, 6.070075757575758, 7.916666666666667)·
No conflict with listed train 12393, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12393)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12397) and no_time_overlap(0.0, 1.0, 2.121212121212121, 4.166666666666668)·
No conflict with listed train 12397, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12397)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12417) and no_time_overlap(0.0, 1.0, 4.784090909090909, 7.0)·
No conflict with listed train 12417, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12417)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12419) and no_time_overlap(0.0, 1.0, 12.397727272727273, 15.0)·
No conflict with listed train 12419, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12419)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12423) and no_time_overlap(0.0, 1.0, 8.625, 10.5)·
No conflict with listed train 12423, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12423)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12451) and no_time_overlap(0.0, 1.0, 3.871212121212121, 5.916666666666668)·
No conflict with listed train 12451, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12451)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12453) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12453, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12453)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12553) and no_time_overlap(0.0, 1.0, 4.1439393939393945, 6.416666666666668)·
No conflict with listed train 12553, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12553)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12555) and no_time_overlap(0.0, 1.0, 3.25, 5.25)·
No conflict with listed train 12555, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12555)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12559) and no_time_overlap(0.0, 1.0, 6.568181818181818, 8.5)·
No conflict with listed train 12559, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12559)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12561) and no_time_overlap(0.0, 1.0, 13.676136363636363, 15.75)·
No conflict with listed train 12561, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12561)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12565) and no_time_overlap(0.0, 1.0, 2.924242424242422, 5.083333333333332)·
No conflict with listed train 12565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 12581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12877) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12877, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12877)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 13007) and no_time_overlap(0.0, 1.0, 15.916666666666668, 19.666666666666668)·
No conflict with listed train 13007, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,13007)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 14037) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 14037, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,14037)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 14619) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 14619, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,14619)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 15565) and no_time_overlap(0.0, 1.0, 4.198863636363637, 6.5)·
No conflict with listed train 15565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,15565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20407) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20407, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20407)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20801) and no_time_overlap(0.0, 1.0, 9.301136363636363, 12.0)·
No conflict with listed train 20801, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20801)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20817) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 20817, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20817)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20839) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20839, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20839)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22361) and no_time_overlap(0.0, 1.0, 10.212121212121211, 13.166666666666666)·
No conflict with listed train 22361, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22361)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22415) and no_time_overlap(0.0, 1.0, 12.520833333333334, 14.083333333333334)·
No conflict with listed train 22415, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22415)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22435) and no_time_overlap(0.0, 1.0, 21.477272727272727, 23.0)·
No conflict with listed train 22435, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22435)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22449) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 22449, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22449)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 22581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22811) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22811, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22811)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22823) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22823, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22823)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Minimum Distance Safety Buffer
timetable_complete_for_exposure(NDLS_CNB_SEC1, UP_LINE)·
Exposure to unlisted trains is unknown: no timetable completeness evidence covers this section, track line, and scheduled interval.·
Traction Power Isolation Rule
not_traction_work(WO-26027-019) or power_isolated(WO-26027-019)·
Work WO-26027-019 is not traction work; the traction isolation rule does not apply.·
Scheduled Block Time Validity
0 <= 0.0 < 1.0 <= 24·
Work WO-26027-021 has a valid scheduled time interval.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12003) and no_time_overlap(0.0, 1.0, 20.53030303030303, 22.416666666666668)·
No conflict with listed train 12003, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12003)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12033) and no_time_overlap(0.0, 1.0, 9.515151515151516, 11.333333333333334)·
No conflict with listed train 12033, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12033)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12259) and no_time_overlap(0.0, 1.0, 9.125, 11.0)·
No conflict with listed train 12259, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12259)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12273) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12273, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12273)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12281) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12281, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12281)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12301) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12301, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12301)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12303) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12303, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12303)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12305) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12305, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12305)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12309) and no_time_overlap(0.0, 1.0, 5.8484848484848495, 7.666666666666668)·
No conflict with listed train 12309, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12309)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12313) and no_time_overlap(0.0, 1.0, 8.958333333333334, 10.833333333333334)·
No conflict with listed train 12313, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12313)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12349) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 12349, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12349)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12381) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12381, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12381)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12393) and no_time_overlap(0.0, 1.0, 6.070075757575758, 7.916666666666667)·
No conflict with listed train 12393, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12393)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12397) and no_time_overlap(0.0, 1.0, 2.121212121212121, 4.166666666666668)·
No conflict with listed train 12397, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12397)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12417) and no_time_overlap(0.0, 1.0, 4.784090909090909, 7.0)·
No conflict with listed train 12417, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12417)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12419) and no_time_overlap(0.0, 1.0, 12.397727272727273, 15.0)·
No conflict with listed train 12419, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12419)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12423) and no_time_overlap(0.0, 1.0, 8.625, 10.5)·
No conflict with listed train 12423, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12423)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12451) and no_time_overlap(0.0, 1.0, 3.871212121212121, 5.916666666666668)·
No conflict with listed train 12451, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12451)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12453) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12453, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12453)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12553) and no_time_overlap(0.0, 1.0, 4.1439393939393945, 6.416666666666668)·
No conflict with listed train 12553, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12553)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12555) and no_time_overlap(0.0, 1.0, 3.25, 5.25)·
No conflict with listed train 12555, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12555)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12559) and no_time_overlap(0.0, 1.0, 6.568181818181818, 8.5)·
No conflict with listed train 12559, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12559)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12561) and no_time_overlap(0.0, 1.0, 13.676136363636363, 15.75)·
No conflict with listed train 12561, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12561)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12565) and no_time_overlap(0.0, 1.0, 2.924242424242422, 5.083333333333332)·
No conflict with listed train 12565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 12581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12877) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12877, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12877)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 13007) and no_time_overlap(0.0, 1.0, 15.916666666666668, 19.666666666666668)·
No conflict with listed train 13007, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,13007)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 14037) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 14037, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,14037)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 14619) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 14619, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,14619)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 15565) and no_time_overlap(0.0, 1.0, 4.198863636363637, 6.5)·
No conflict with listed train 15565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,15565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20407) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20407, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20407)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20801) and no_time_overlap(0.0, 1.0, 9.301136363636363, 12.0)·
No conflict with listed train 20801, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20801)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20817) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 20817, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20817)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20839) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20839, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20839)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22361) and no_time_overlap(0.0, 1.0, 10.212121212121211, 13.166666666666666)·
No conflict with listed train 22361, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22361)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22415) and no_time_overlap(0.0, 1.0, 12.520833333333334, 14.083333333333334)·
No conflict with listed train 22415, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22415)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22435) and no_time_overlap(0.0, 1.0, 21.477272727272727, 23.0)·
No conflict with listed train 22435, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22435)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22449) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 22449, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22449)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 22581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22811) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22811, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22811)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22823) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22823, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22823)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Minimum Distance Safety Buffer
timetable_complete_for_exposure(NDLS_CNB_SEC1, UP_LINE)·
Exposure to unlisted trains is unknown: no timetable completeness evidence covers this section, track line, and scheduled interval.·
Traction Power Isolation Rule
not_traction_work(WO-26027-021) or power_isolated(WO-26027-021)·
Work WO-26027-021 is not traction work; the traction isolation rule does not apply."
```

```
Error: unscheduled count / warning shown

expect(received).toMatch(expected)

Expected pattern: /unscheduled|not scheduled|could not be scheduled/i
Received string:  "SymbIO-Block Dashboard·
Symbolic CSP & FOL railway maintenance block scheduling·
API online
Audit Log
171
Offline simulation scenarios·
Saved scenarios stay in this browser. Running a comparison sends the selected scenario to the experimental API; results are not saved. Do not enter credentials, evidence, or operational railway data. This prototype is not operationally authorized.·
Reload saved
Save scenarios
New scenario name
Scenario sections·
NDLS_CNB · New Delhi - Kanpur Central·
NDLS_CNB_SEC1
NDLS_CNB_SEC2
NDLS_CNB_SEC3·
HWH_PURI · Howrah - Puri·
HWH_PURI_SEC1
HWH_PURI_SEC2
HWH_PURI_SEC3·
BCT_AMD · Mumbai Central - Ahmedabad·
BCT_AMD_SEC1
BCT_AMD_SEC2
BCT_AMD_SEC3·
Section IDs come from the backend route list. Existing work orders and train windows must be moved explicitly if you remove their current section.·
Create·
No saved scenarios yet.·
Create an offline scenario above. It will remain a draft until saved.·
Scenario solver comparison·
Offline, non-operational simulation. This runs the selected browser-local scenario (including any unsaved edits) against the experimental API; it does not change saved scenario storage or assess railway safety.·
Run comparison·
Create or select a scenario above to compare it.·
Corridor
NDLS_CNB · New Delhi - Kanpur Central
HWH_PURI · Howrah - Puri
BCT_AMD · Mumbai Central - Ahmedabad
Section IDs (comma separated)
Horizon (hrs)
AC-3 pruning
Simulated annealing
Timetable
Work Orders
30
Generate Schedule
Search Space Pruned (AC-3)
92.0%
Safety Rule Compliance
—
Track Hours Saved
1.0 h
1 co-location merges
1 Parallel Maintenance Requests Bundled into Co-Located Block Windows
Solver Speed
1 ms
2/30 blocks scheduled
Time-Space Schedule · status: safety_unverified
00:00
NDLS_CNB_SEC1
UP LINE
SIG
WO-26027-019
ENG
WO-26027-021
DOWN LINE
12350
12418
12452
12582
14038
14620
22450
22582
NDLS_CNB_SEC2
UP LINE
12397
12565
DOWN LINE
12418
12554
12556
12562
12582
15566
20802
22582
NDLS_CNB_SEC3
UP LINE
12273
12281
12303
12381
12397
12417
12451
12553
12555
12565
15565
DOWN LINE
12260
12554
12560
12562
15566
22362
Train occupancy
ENG = ENGINEERING
SIG = SIGNALLING
TRC = TRACTION
Striped = co-located block
Work Order Inspection·
Click a maintenance block on the Gantt chart to inspect its work order.·
FOL Audit Log
All rules (171)
WO-26027-019 — NDLS_CNB_SEC1 UP LINE 0–1h
WO-26027-021 — NDLS_CNB_SEC1 UP LINE 0–1h
AC3DomainPruning
all_candidate_domains_nonempty_after_ac3·
AC-3 removed 1 of 3 candidate starts remaining after train-conflict filtering.·
Scheduled Block Time Validity
0 <= 0.0 < 1.0 <= 24·
Work WO-26027-019 has a valid scheduled time interval.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12003) and no_time_overlap(0.0, 1.0, 20.53030303030303, 22.416666666666668)·
No conflict with listed train 12003, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12003)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12033) and no_time_overlap(0.0, 1.0, 9.515151515151516, 11.333333333333334)·
No conflict with listed train 12033, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12033)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12259) and no_time_overlap(0.0, 1.0, 9.125, 11.0)·
No conflict with listed train 12259, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12259)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12273) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12273, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12273)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12281) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12281, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12281)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12301) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12301, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12301)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12303) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12303, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12303)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12305) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12305, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12305)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12309) and no_time_overlap(0.0, 1.0, 5.8484848484848495, 7.666666666666668)·
No conflict with listed train 12309, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12309)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12313) and no_time_overlap(0.0, 1.0, 8.958333333333334, 10.833333333333334)·
No conflict with listed train 12313, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12313)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12349) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 12349, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12349)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12381) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12381, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12381)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12393) and no_time_overlap(0.0, 1.0, 6.070075757575758, 7.916666666666667)·
No conflict with listed train 12393, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12393)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12397) and no_time_overlap(0.0, 1.0, 2.121212121212121, 4.166666666666668)·
No conflict with listed train 12397, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12397)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12417) and no_time_overlap(0.0, 1.0, 4.784090909090909, 7.0)·
No conflict with listed train 12417, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12417)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12419) and no_time_overlap(0.0, 1.0, 12.397727272727273, 15.0)·
No conflict with listed train 12419, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12419)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12423) and no_time_overlap(0.0, 1.0, 8.625, 10.5)·
No conflict with listed train 12423, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12423)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12451) and no_time_overlap(0.0, 1.0, 3.871212121212121, 5.916666666666668)·
No conflict with listed train 12451, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12451)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12453) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12453, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12453)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12553) and no_time_overlap(0.0, 1.0, 4.1439393939393945, 6.416666666666668)·
No conflict with listed train 12553, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12553)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12555) and no_time_overlap(0.0, 1.0, 3.25, 5.25)·
No conflict with listed train 12555, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12555)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12559) and no_time_overlap(0.0, 1.0, 6.568181818181818, 8.5)·
No conflict with listed train 12559, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12559)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12561) and no_time_overlap(0.0, 1.0, 13.676136363636363, 15.75)·
No conflict with listed train 12561, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12561)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12565) and no_time_overlap(0.0, 1.0, 2.924242424242422, 5.083333333333332)·
No conflict with listed train 12565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 12581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 12877) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12877, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,12877)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 13007) and no_time_overlap(0.0, 1.0, 15.916666666666668, 19.666666666666668)·
No conflict with listed train 13007, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,13007)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 14037) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 14037, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,14037)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 14619) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 14619, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,14619)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 15565) and no_time_overlap(0.0, 1.0, 4.198863636363637, 6.5)·
No conflict with listed train 15565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,15565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20407) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20407, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20407)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20801) and no_time_overlap(0.0, 1.0, 9.301136363636363, 12.0)·
No conflict with listed train 20801, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20801)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20817) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 20817, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20817)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 20839) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20839, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,20839)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22361) and no_time_overlap(0.0, 1.0, 10.212121212121211, 13.166666666666666)·
No conflict with listed train 22361, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22361)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22415) and no_time_overlap(0.0, 1.0, 12.520833333333334, 14.083333333333334)·
No conflict with listed train 22415, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22415)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22435) and no_time_overlap(0.0, 1.0, 21.477272727272727, 23.0)·
No conflict with listed train 22435, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22435)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22449) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 22449, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22449)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 22581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22811) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22811, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22811)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-019, 22823) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22823, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-019,22823)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Minimum Distance Safety Buffer
timetable_complete_for_exposure(NDLS_CNB_SEC1, UP_LINE)·
Exposure to unlisted trains is unknown: no timetable completeness evidence covers this section, track line, and scheduled interval.·
Traction Power Isolation Rule
not_traction_work(WO-26027-019) or power_isolated(WO-26027-019)·
Work WO-26027-019 is not traction work; the traction isolation rule does not apply.·
Scheduled Block Time Validity
0 <= 0.0 < 1.0 <= 24·
Work WO-26027-021 has a valid scheduled time interval.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12003) and no_time_overlap(0.0, 1.0, 20.53030303030303, 22.416666666666668)·
No conflict with listed train 12003, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12003)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12033) and no_time_overlap(0.0, 1.0, 9.515151515151516, 11.333333333333334)·
No conflict with listed train 12033, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12033)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12259) and no_time_overlap(0.0, 1.0, 9.125, 11.0)·
No conflict with listed train 12259, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12259)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12273) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12273, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12273)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12281) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)·
No conflict with listed train 12281, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12281)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12301) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12301, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12301)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12303) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12303, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12303)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12305) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)·
No conflict with listed train 12305, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12305)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12309) and no_time_overlap(0.0, 1.0, 5.8484848484848495, 7.666666666666668)·
No conflict with listed train 12309, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12309)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12313) and no_time_overlap(0.0, 1.0, 8.958333333333334, 10.833333333333334)·
No conflict with listed train 12313, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12313)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12349) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 12349, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12349)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12381) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)·
No conflict with listed train 12381, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12381)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12393) and no_time_overlap(0.0, 1.0, 6.070075757575758, 7.916666666666667)·
No conflict with listed train 12393, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12393)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12397) and no_time_overlap(0.0, 1.0, 2.121212121212121, 4.166666666666668)·
No conflict with listed train 12397, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12397)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12417) and no_time_overlap(0.0, 1.0, 4.784090909090909, 7.0)·
No conflict with listed train 12417, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12417)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12419) and no_time_overlap(0.0, 1.0, 12.397727272727273, 15.0)·
No conflict with listed train 12419, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12419)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12423) and no_time_overlap(0.0, 1.0, 8.625, 10.5)·
No conflict with listed train 12423, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12423)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12451) and no_time_overlap(0.0, 1.0, 3.871212121212121, 5.916666666666668)·
No conflict with listed train 12451, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12451)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12453) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12453, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12453)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12553) and no_time_overlap(0.0, 1.0, 4.1439393939393945, 6.416666666666668)·
No conflict with listed train 12553, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12553)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12555) and no_time_overlap(0.0, 1.0, 3.25, 5.25)·
No conflict with listed train 12555, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12555)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12559) and no_time_overlap(0.0, 1.0, 6.568181818181818, 8.5)·
No conflict with listed train 12559, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12559)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12561) and no_time_overlap(0.0, 1.0, 13.676136363636363, 15.75)·
No conflict with listed train 12561, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12561)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12565) and no_time_overlap(0.0, 1.0, 2.924242424242422, 5.083333333333332)·
No conflict with listed train 12565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 12581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 12877) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 12877, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,12877)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 13007) and no_time_overlap(0.0, 1.0, 15.916666666666668, 19.666666666666668)·
No conflict with listed train 13007, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,13007)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 14037) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)·
No conflict with listed train 14037, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,14037)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 14619) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 14619, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,14619)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 15565) and no_time_overlap(0.0, 1.0, 4.198863636363637, 6.5)·
No conflict with listed train 15565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,15565)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20407) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20407, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20407)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20801) and no_time_overlap(0.0, 1.0, 9.301136363636363, 12.0)·
No conflict with listed train 20801, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20801)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20817) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 20817, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20817)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 20839) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)·
No conflict with listed train 20839, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,20839)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22361) and no_time_overlap(0.0, 1.0, 10.212121212121211, 13.166666666666666)·
No conflict with listed train 22361, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22361)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22415) and no_time_overlap(0.0, 1.0, 12.520833333333334, 14.083333333333334)·
No conflict with listed train 22415, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22415)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22435) and no_time_overlap(0.0, 1.0, 21.477272727272727, 23.0)·
No conflict with listed train 22435, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22435)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22449) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)·
No conflict with listed train 22449, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22449)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)·
No conflict with listed train 22581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22581)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22811) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22811, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22811)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Passenger Train Clearance Invariant
same_section(WO-26027-021, 22823) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)·
No conflict with listed train 22823, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.·
Minimum Distance Safety Buffer
no_concurrent_exposure(WO-26027-021,22823)·
The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.·
Minimum Distance Safety Buffer
timetable_complete_for_exposure(NDLS_CNB_SEC1, UP_LINE)·
Exposure to unlisted trains is unknown: no timetable completeness evidence covers this section, track line, and scheduled interval.·
Traction Power Isolation Rule
not_traction_work(WO-26027-021) or power_isolated(WO-26027-021)·
Work WO-26027-021 is not traction work; the traction isolation rule does not apply."
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - main [ref=e2]:
    - generic [ref=e3]:
      - generic [ref=e4]:
        - heading "SymbIO-Block Dashboard" [level=1] [ref=e5]
        - paragraph [ref=e6]: Symbolic CSP & FOL railway maintenance block scheduling
      - generic [ref=e7]:
        - generic [ref=e8]: API online
        - button "Audit Log 171" [ref=e10]:
          - text: Audit Log
          - generic [ref=e14]: "171"
    - generic [ref=e15]:
      - generic [ref=e16]:
        - generic [ref=e17]:
          - heading "Offline simulation scenarios" [level=2] [ref=e18]
          - paragraph [ref=e19]: Saved scenarios stay in this browser. Running a comparison sends the selected scenario to the experimental API; results are not saved. Do not enter credentials, evidence, or operational railway data. This prototype is not operationally authorized.
        - generic [ref=e20]:
          - button "Reload saved" [ref=e21]
          - button "Save scenarios" [disabled] [ref=e27]
      - generic [ref=e32]:
        - generic [ref=e33]:
          - text: New scenario name
          - textbox "New scenario name" [ref=e34]:
            - /placeholder: My maintenance scenario
        - group "Scenario sections" [ref=e35]:
          - generic [ref=e37]:
            - generic [ref=e38]:
              - paragraph [ref=e39]: NDLS_CNB · New Delhi - Kanpur Central
              - generic [ref=e40]:
                - checkbox "NDLS_CNB_SEC1" [ref=e41]
                - generic [ref=e42]: NDLS_CNB_SEC1
              - generic [ref=e43]:
                - checkbox "NDLS_CNB_SEC2" [ref=e44]
                - generic [ref=e45]: NDLS_CNB_SEC2
              - generic [ref=e46]:
                - checkbox "NDLS_CNB_SEC3" [ref=e47]
                - generic [ref=e48]: NDLS_CNB_SEC3
            - generic [ref=e49]:
              - paragraph [ref=e50]: HWH_PURI · Howrah - Puri
              - generic [ref=e51]:
                - checkbox "HWH_PURI_SEC1" [ref=e52]
                - generic [ref=e53]: HWH_PURI_SEC1
              - generic [ref=e54]:
                - checkbox "HWH_PURI_SEC2" [ref=e55]
                - generic [ref=e56]: HWH_PURI_SEC2
              - generic [ref=e57]:
                - checkbox "HWH_PURI_SEC3" [ref=e58]
                - generic [ref=e59]: HWH_PURI_SEC3
            - generic [ref=e60]:
              - paragraph [ref=e61]: BCT_AMD · Mumbai Central - Ahmedabad
              - generic [ref=e62]:
                - checkbox "BCT_AMD_SEC1" [ref=e63]
                - generic [ref=e64]: BCT_AMD_SEC1
              - generic [ref=e65]:
                - checkbox "BCT_AMD_SEC2" [ref=e66]
                - generic [ref=e67]: BCT_AMD_SEC2
              - generic [ref=e68]:
                - checkbox "BCT_AMD_SEC3" [ref=e69]
                - generic [ref=e70]: BCT_AMD_SEC3
          - paragraph [ref=e71]: Section IDs come from the backend route list. Existing work orders and train windows must be moved explicitly if you remove their current section.
        - button "Create" [ref=e72]
      - generic [ref=e74]:
        - paragraph [ref=e75]: No saved scenarios yet.
        - paragraph [ref=e76]: Create an offline scenario above. It will remain a draft until saved.
    - region "Experimental scenario comparison" [ref=e77]:
      - generic [ref=e78]:
        - generic [ref=e79]:
          - heading "Scenario solver comparison" [level=2] [ref=e80]
          - paragraph [ref=e81]: Offline, non-operational simulation. This runs the selected browser-local scenario (including any unsaved edits) against the experimental API; it does not change saved scenario storage or assess railway safety.
        - button "Run comparison" [disabled] [ref=e82]
      - paragraph [ref=e85]: Create or select a scenario above to compare it.
    - generic [ref=e86]:
      - generic [ref=e87]:
        - text: Corridor
        - combobox "Corridor" [ref=e88]:
          - option "NDLS_CNB · New Delhi - Kanpur Central" [selected]
          - option "HWH_PURI · Howrah - Puri"
          - option "BCT_AMD · Mumbai Central - Ahmedabad"
      - generic [ref=e89]:
        - text: Section IDs (comma separated)
        - textbox "Section IDs (comma separated)" [ref=e90]: NDLS_CNB_SEC1, NDLS_CNB_SEC2, NDLS_CNB_SEC3
      - generic [ref=e91]:
        - text: Horizon (hrs)
        - spinbutton "Horizon (hrs)" [ref=e92]: "1"
      - generic [ref=e93]:
        - checkbox "AC-3 pruning" [checked] [ref=e94]
        - text: AC-3 pruning
      - generic [ref=e95]:
        - checkbox "Simulated annealing" [checked] [ref=e96]
        - text: Simulated annealing
      - generic "Upload a JSON array of train occupancy windows" [ref=e97] [cursor=pointer]: Timetable
      - button "Work Orders 30" [ref=e101]:
        - text: Work Orders
        - generic [ref=e105]: "30"
      - button "Reload trains" [ref=e106]
      - button "Generate Schedule" [ref=e112]
    - generic [ref=e115]:
      - generic [ref=e116]:
        - generic [ref=e117]: Search Space Pruned (AC-3)
        - generic [ref=e124]: 92.0%
      - generic [ref=e125]:
        - generic [ref=e126]: Safety Rule Compliance
        - generic [ref=e130]: —
      - generic [ref=e131]:
        - generic [ref=e132]: Track Hours Saved
        - generic [ref=e136]: 1.0 h
        - generic [ref=e137]: 1 co-location merges
        - generic [ref=e138]: 1 Parallel Maintenance Requests Bundled into Co-Located Block Windows
      - generic [ref=e139]:
        - generic [ref=e140]: Solver Speed
        - generic [ref=e144]: 1 ms
        - generic [ref=e145]: 2/30 blocks scheduled
    - generic [ref=e146]:
      - 'heading "Time-Space Schedule · status: safety_unverified" [level=2] [ref=e147]':
        - text: Time-Space Schedule
        - generic [ref=e148]: "· status: safety_unverified"
      - generic [ref=e150]:
        - generic [ref=e151]: 00:00
        - generic [ref=e155]:
          - generic [ref=e156]: NDLS_CNB_SEC1
          - generic [ref=e157]:
            - generic [ref=e158]:
              - generic: Up line
              - button "SIG WO-26027-019" [ref=e160]:
                - generic [ref=e161]: SIG
                - generic [ref=e162]: WO-26027-019
              - button "ENG WO-26027-021" [ref=e163]:
                - generic [ref=e164]: ENG
                - generic [ref=e165]: WO-26027-021
            - generic [ref=e166]:
              - generic: Down line
              - generic [ref=e168]: "12350"
              - generic [ref=e169]: "12418"
              - generic [ref=e170]: "12452"
              - generic [ref=e171]: "12582"
              - generic [ref=e172]: "14038"
              - generic [ref=e173]: "14620"
              - generic [ref=e174]: "22450"
              - generic [ref=e175]: "22582"
        - generic [ref=e176]:
          - generic [ref=e177]: NDLS_CNB_SEC2
          - generic [ref=e178]:
            - generic [ref=e179]:
              - generic: Up line
              - generic [ref=e181]: "12397"
              - generic [ref=e182]: "12565"
            - generic [ref=e183]:
              - generic: Down line
              - generic [ref=e185]: "12418"
              - generic [ref=e186]: "12554"
              - generic [ref=e187]: "12556"
              - generic [ref=e188]: "12562"
              - generic [ref=e189]: "12582"
              - generic [ref=e190]: "15566"
              - generic [ref=e191]: "20802"
              - generic [ref=e192]: "22582"
        - generic [ref=e193]:
          - generic [ref=e194]: NDLS_CNB_SEC3
          - generic [ref=e195]:
            - generic [ref=e196]:
              - generic: Up line
              - generic [ref=e198]: "12273"
              - generic [ref=e199]: "12281"
              - generic [ref=e200]: "12303"
              - generic [ref=e201]: "12381"
              - generic [ref=e202]: "12397"
              - generic [ref=e203]: "12417"
              - generic [ref=e204]: "12451"
              - generic [ref=e205]: "12553"
              - generic [ref=e206]: "12555"
              - generic [ref=e207]: "12565"
              - generic [ref=e208]: "15565"
            - generic [ref=e209]:
              - generic: Down line
              - generic [ref=e211]: "12260"
              - generic [ref=e212]: "12554"
              - generic [ref=e213]: "12560"
              - generic [ref=e214]: "12562"
              - generic [ref=e215]: "15566"
              - generic [ref=e216]: "22362"
        - generic [ref=e217]:
          - generic [ref=e218]: Train occupancy
          - generic [ref=e220]: ENG = ENGINEERING
          - generic [ref=e222]: SIG = SIGNALLING
          - generic [ref=e224]: TRC = TRACTION
          - generic [ref=e226]: Striped = co-located block
    - generic [ref=e227]:
      - heading "Work Order Inspection" [level=2] [ref=e228]
      - paragraph [ref=e229]: Click a maintenance block on the Gantt chart to inspect its work order.
    - complementary [aria-hidden] [ref=e230]:
      - generic [ref=e231]:
        - heading [level=2] [ref=e232]: FOL Audit Log
        - button [ref=e233]
      - combobox [ref=e238]
      - generic [ref=e239]:
        - generic [ref=e240]:
          - generic [ref=e241]: AC3DomainPruning
          - code [ref=e246]: all_candidate_domains_nonempty_after_ac3
          - paragraph [ref=e247]: AC-3 removed 1 of 3 candidate starts remaining after train-conflict filtering.
        - generic [ref=e248]:
          - generic [ref=e249]: Scheduled Block Time Validity
          - code [ref=e253]: 0 <= 0.0 < 1.0 <= 24
          - paragraph [ref=e254]: Work WO-26027-019 has a valid scheduled time interval.
        - generic [ref=e255]:
          - generic [ref=e256]: Passenger Train Clearance Invariant
          - code [ref=e260]: same_section(WO-26027-019, 12003) and no_time_overlap(0.0, 1.0, 20.53030303030303, 22.416666666666668)
          - paragraph [ref=e261]: No conflict with listed train 12003, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e262]:
          - generic [ref=e263]: Minimum Distance Safety Buffer
          - code [ref=e267]: no_concurrent_exposure(WO-26027-019,12003)
          - paragraph [ref=e268]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e269]:
          - generic [ref=e270]: Passenger Train Clearance Invariant
          - code [ref=e274]: same_section(WO-26027-019, 12033) and no_time_overlap(0.0, 1.0, 9.515151515151516, 11.333333333333334)
          - paragraph [ref=e275]: No conflict with listed train 12033, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e276]:
          - generic [ref=e277]: Minimum Distance Safety Buffer
          - code [ref=e281]: no_concurrent_exposure(WO-26027-019,12033)
          - paragraph [ref=e282]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e283]:
          - generic [ref=e284]: Passenger Train Clearance Invariant
          - code [ref=e288]: same_section(WO-26027-019, 12259) and no_time_overlap(0.0, 1.0, 9.125, 11.0)
          - paragraph [ref=e289]: No conflict with listed train 12259, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e290]:
          - generic [ref=e291]: Minimum Distance Safety Buffer
          - code [ref=e295]: no_concurrent_exposure(WO-26027-019,12259)
          - paragraph [ref=e296]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e297]:
          - generic [ref=e298]: Passenger Train Clearance Invariant
          - code [ref=e302]: same_section(WO-26027-019, 12273) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)
          - paragraph [ref=e303]: No conflict with listed train 12273, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e304]:
          - generic [ref=e305]: Minimum Distance Safety Buffer
          - code [ref=e309]: no_concurrent_exposure(WO-26027-019,12273)
          - paragraph [ref=e310]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e311]:
          - generic [ref=e312]: Passenger Train Clearance Invariant
          - code [ref=e316]: same_section(WO-26027-019, 12281) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)
          - paragraph [ref=e317]: No conflict with listed train 12281, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e318]:
          - generic [ref=e319]: Minimum Distance Safety Buffer
          - code [ref=e323]: no_concurrent_exposure(WO-26027-019,12281)
          - paragraph [ref=e324]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e325]:
          - generic [ref=e326]: Passenger Train Clearance Invariant
          - code [ref=e330]: same_section(WO-26027-019, 12301) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)
          - paragraph [ref=e331]: No conflict with listed train 12301, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e332]:
          - generic [ref=e333]: Minimum Distance Safety Buffer
          - code [ref=e337]: no_concurrent_exposure(WO-26027-019,12301)
          - paragraph [ref=e338]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e339]:
          - generic [ref=e340]: Passenger Train Clearance Invariant
          - code [ref=e344]: same_section(WO-26027-019, 12303) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)
          - paragraph [ref=e345]: No conflict with listed train 12303, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e346]:
          - generic [ref=e347]: Minimum Distance Safety Buffer
          - code [ref=e351]: no_concurrent_exposure(WO-26027-019,12303)
          - paragraph [ref=e352]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e353]:
          - generic [ref=e354]: Passenger Train Clearance Invariant
          - code [ref=e358]: same_section(WO-26027-019, 12305) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)
          - paragraph [ref=e359]: No conflict with listed train 12305, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e360]:
          - generic [ref=e361]: Minimum Distance Safety Buffer
          - code [ref=e365]: no_concurrent_exposure(WO-26027-019,12305)
          - paragraph [ref=e366]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e367]:
          - generic [ref=e368]: Passenger Train Clearance Invariant
          - code [ref=e372]: same_section(WO-26027-019, 12309) and no_time_overlap(0.0, 1.0, 5.8484848484848495, 7.666666666666668)
          - paragraph [ref=e373]: No conflict with listed train 12309, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e374]:
          - generic [ref=e375]: Minimum Distance Safety Buffer
          - code [ref=e379]: no_concurrent_exposure(WO-26027-019,12309)
          - paragraph [ref=e380]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e381]:
          - generic [ref=e382]: Passenger Train Clearance Invariant
          - code [ref=e386]: same_section(WO-26027-019, 12313) and no_time_overlap(0.0, 1.0, 8.958333333333334, 10.833333333333334)
          - paragraph [ref=e387]: No conflict with listed train 12313, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e388]:
          - generic [ref=e389]: Minimum Distance Safety Buffer
          - code [ref=e393]: no_concurrent_exposure(WO-26027-019,12313)
          - paragraph [ref=e394]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e395]:
          - generic [ref=e396]: Passenger Train Clearance Invariant
          - code [ref=e400]: same_section(WO-26027-019, 12349) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)
          - paragraph [ref=e401]: No conflict with listed train 12349, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e402]:
          - generic [ref=e403]: Minimum Distance Safety Buffer
          - code [ref=e407]: no_concurrent_exposure(WO-26027-019,12349)
          - paragraph [ref=e408]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e409]:
          - generic [ref=e410]: Passenger Train Clearance Invariant
          - code [ref=e414]: same_section(WO-26027-019, 12381) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)
          - paragraph [ref=e415]: No conflict with listed train 12381, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e416]:
          - generic [ref=e417]: Minimum Distance Safety Buffer
          - code [ref=e421]: no_concurrent_exposure(WO-26027-019,12381)
          - paragraph [ref=e422]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e423]:
          - generic [ref=e424]: Passenger Train Clearance Invariant
          - code [ref=e428]: same_section(WO-26027-019, 12393) and no_time_overlap(0.0, 1.0, 6.070075757575758, 7.916666666666667)
          - paragraph [ref=e429]: No conflict with listed train 12393, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e430]:
          - generic [ref=e431]: Minimum Distance Safety Buffer
          - code [ref=e435]: no_concurrent_exposure(WO-26027-019,12393)
          - paragraph [ref=e436]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e437]:
          - generic [ref=e438]: Passenger Train Clearance Invariant
          - code [ref=e442]: same_section(WO-26027-019, 12397) and no_time_overlap(0.0, 1.0, 2.121212121212121, 4.166666666666668)
          - paragraph [ref=e443]: No conflict with listed train 12397, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e444]:
          - generic [ref=e445]: Minimum Distance Safety Buffer
          - code [ref=e449]: no_concurrent_exposure(WO-26027-019,12397)
          - paragraph [ref=e450]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e451]:
          - generic [ref=e452]: Passenger Train Clearance Invariant
          - code [ref=e456]: same_section(WO-26027-019, 12417) and no_time_overlap(0.0, 1.0, 4.784090909090909, 7.0)
          - paragraph [ref=e457]: No conflict with listed train 12417, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e458]:
          - generic [ref=e459]: Minimum Distance Safety Buffer
          - code [ref=e463]: no_concurrent_exposure(WO-26027-019,12417)
          - paragraph [ref=e464]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e465]:
          - generic [ref=e466]: Passenger Train Clearance Invariant
          - code [ref=e470]: same_section(WO-26027-019, 12419) and no_time_overlap(0.0, 1.0, 12.397727272727273, 15.0)
          - paragraph [ref=e471]: No conflict with listed train 12419, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e472]:
          - generic [ref=e473]: Minimum Distance Safety Buffer
          - code [ref=e477]: no_concurrent_exposure(WO-26027-019,12419)
          - paragraph [ref=e478]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e479]:
          - generic [ref=e480]: Passenger Train Clearance Invariant
          - code [ref=e484]: same_section(WO-26027-019, 12423) and no_time_overlap(0.0, 1.0, 8.625, 10.5)
          - paragraph [ref=e485]: No conflict with listed train 12423, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e486]:
          - generic [ref=e487]: Minimum Distance Safety Buffer
          - code [ref=e491]: no_concurrent_exposure(WO-26027-019,12423)
          - paragraph [ref=e492]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e493]:
          - generic [ref=e494]: Passenger Train Clearance Invariant
          - code [ref=e498]: same_section(WO-26027-019, 12451) and no_time_overlap(0.0, 1.0, 3.871212121212121, 5.916666666666668)
          - paragraph [ref=e499]: No conflict with listed train 12451, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e500]:
          - generic [ref=e501]: Minimum Distance Safety Buffer
          - code [ref=e505]: no_concurrent_exposure(WO-26027-019,12451)
          - paragraph [ref=e506]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e507]:
          - generic [ref=e508]: Passenger Train Clearance Invariant
          - code [ref=e512]: same_section(WO-26027-019, 12453) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)
          - paragraph [ref=e513]: No conflict with listed train 12453, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e514]:
          - generic [ref=e515]: Minimum Distance Safety Buffer
          - code [ref=e519]: no_concurrent_exposure(WO-26027-019,12453)
          - paragraph [ref=e520]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e521]:
          - generic [ref=e522]: Passenger Train Clearance Invariant
          - code [ref=e526]: same_section(WO-26027-019, 12553) and no_time_overlap(0.0, 1.0, 4.1439393939393945, 6.416666666666668)
          - paragraph [ref=e527]: No conflict with listed train 12553, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e528]:
          - generic [ref=e529]: Minimum Distance Safety Buffer
          - code [ref=e533]: no_concurrent_exposure(WO-26027-019,12553)
          - paragraph [ref=e534]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e535]:
          - generic [ref=e536]: Passenger Train Clearance Invariant
          - code [ref=e540]: same_section(WO-26027-019, 12555) and no_time_overlap(0.0, 1.0, 3.25, 5.25)
          - paragraph [ref=e541]: No conflict with listed train 12555, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e542]:
          - generic [ref=e543]: Minimum Distance Safety Buffer
          - code [ref=e547]: no_concurrent_exposure(WO-26027-019,12555)
          - paragraph [ref=e548]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e549]:
          - generic [ref=e550]: Passenger Train Clearance Invariant
          - code [ref=e554]: same_section(WO-26027-019, 12559) and no_time_overlap(0.0, 1.0, 6.568181818181818, 8.5)
          - paragraph [ref=e555]: No conflict with listed train 12559, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e556]:
          - generic [ref=e557]: Minimum Distance Safety Buffer
          - code [ref=e561]: no_concurrent_exposure(WO-26027-019,12559)
          - paragraph [ref=e562]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e563]:
          - generic [ref=e564]: Passenger Train Clearance Invariant
          - code [ref=e568]: same_section(WO-26027-019, 12561) and no_time_overlap(0.0, 1.0, 13.676136363636363, 15.75)
          - paragraph [ref=e569]: No conflict with listed train 12561, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e570]:
          - generic [ref=e571]: Minimum Distance Safety Buffer
          - code [ref=e575]: no_concurrent_exposure(WO-26027-019,12561)
          - paragraph [ref=e576]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e577]:
          - generic [ref=e578]: Passenger Train Clearance Invariant
          - code [ref=e582]: same_section(WO-26027-019, 12565) and no_time_overlap(0.0, 1.0, 2.924242424242422, 5.083333333333332)
          - paragraph [ref=e583]: No conflict with listed train 12565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e584]:
          - generic [ref=e585]: Minimum Distance Safety Buffer
          - code [ref=e589]: no_concurrent_exposure(WO-26027-019,12565)
          - paragraph [ref=e590]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e591]:
          - generic [ref=e592]: Passenger Train Clearance Invariant
          - code [ref=e596]: same_section(WO-26027-019, 12581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)
          - paragraph [ref=e597]: No conflict with listed train 12581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e598]:
          - generic [ref=e599]: Minimum Distance Safety Buffer
          - code [ref=e603]: no_concurrent_exposure(WO-26027-019,12581)
          - paragraph [ref=e604]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e605]:
          - generic [ref=e606]: Passenger Train Clearance Invariant
          - code [ref=e610]: same_section(WO-26027-019, 12877) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)
          - paragraph [ref=e611]: No conflict with listed train 12877, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e612]:
          - generic [ref=e613]: Minimum Distance Safety Buffer
          - code [ref=e617]: no_concurrent_exposure(WO-26027-019,12877)
          - paragraph [ref=e618]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e619]:
          - generic [ref=e620]: Passenger Train Clearance Invariant
          - code [ref=e624]: same_section(WO-26027-019, 13007) and no_time_overlap(0.0, 1.0, 15.916666666666668, 19.666666666666668)
          - paragraph [ref=e625]: No conflict with listed train 13007, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e626]:
          - generic [ref=e627]: Minimum Distance Safety Buffer
          - code [ref=e631]: no_concurrent_exposure(WO-26027-019,13007)
          - paragraph [ref=e632]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e633]:
          - generic [ref=e634]: Passenger Train Clearance Invariant
          - code [ref=e638]: same_section(WO-26027-019, 14037) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)
          - paragraph [ref=e639]: No conflict with listed train 14037, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e640]:
          - generic [ref=e641]: Minimum Distance Safety Buffer
          - code [ref=e645]: no_concurrent_exposure(WO-26027-019,14037)
          - paragraph [ref=e646]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e647]:
          - generic [ref=e648]: Passenger Train Clearance Invariant
          - code [ref=e652]: same_section(WO-26027-019, 14619) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)
          - paragraph [ref=e653]: No conflict with listed train 14619, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e654]:
          - generic [ref=e655]: Minimum Distance Safety Buffer
          - code [ref=e659]: no_concurrent_exposure(WO-26027-019,14619)
          - paragraph [ref=e660]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e661]:
          - generic [ref=e662]: Passenger Train Clearance Invariant
          - code [ref=e666]: same_section(WO-26027-019, 15565) and no_time_overlap(0.0, 1.0, 4.198863636363637, 6.5)
          - paragraph [ref=e667]: No conflict with listed train 15565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e668]:
          - generic [ref=e669]: Minimum Distance Safety Buffer
          - code [ref=e673]: no_concurrent_exposure(WO-26027-019,15565)
          - paragraph [ref=e674]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e675]:
          - generic [ref=e676]: Passenger Train Clearance Invariant
          - code [ref=e680]: same_section(WO-26027-019, 20407) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)
          - paragraph [ref=e681]: No conflict with listed train 20407, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e682]:
          - generic [ref=e683]: Minimum Distance Safety Buffer
          - code [ref=e687]: no_concurrent_exposure(WO-26027-019,20407)
          - paragraph [ref=e688]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e689]:
          - generic [ref=e690]: Passenger Train Clearance Invariant
          - code [ref=e694]: same_section(WO-26027-019, 20801) and no_time_overlap(0.0, 1.0, 9.301136363636363, 12.0)
          - paragraph [ref=e695]: No conflict with listed train 20801, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e696]:
          - generic [ref=e697]: Minimum Distance Safety Buffer
          - code [ref=e701]: no_concurrent_exposure(WO-26027-019,20801)
          - paragraph [ref=e702]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e703]:
          - generic [ref=e704]: Passenger Train Clearance Invariant
          - code [ref=e708]: same_section(WO-26027-019, 20817) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)
          - paragraph [ref=e709]: No conflict with listed train 20817, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e710]:
          - generic [ref=e711]: Minimum Distance Safety Buffer
          - code [ref=e715]: no_concurrent_exposure(WO-26027-019,20817)
          - paragraph [ref=e716]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e717]:
          - generic [ref=e718]: Passenger Train Clearance Invariant
          - code [ref=e722]: same_section(WO-26027-019, 20839) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)
          - paragraph [ref=e723]: No conflict with listed train 20839, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e724]:
          - generic [ref=e725]: Minimum Distance Safety Buffer
          - code [ref=e729]: no_concurrent_exposure(WO-26027-019,20839)
          - paragraph [ref=e730]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e731]:
          - generic [ref=e732]: Passenger Train Clearance Invariant
          - code [ref=e736]: same_section(WO-26027-019, 22361) and no_time_overlap(0.0, 1.0, 10.212121212121211, 13.166666666666666)
          - paragraph [ref=e737]: No conflict with listed train 22361, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e738]:
          - generic [ref=e739]: Minimum Distance Safety Buffer
          - code [ref=e743]: no_concurrent_exposure(WO-26027-019,22361)
          - paragraph [ref=e744]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e745]:
          - generic [ref=e746]: Passenger Train Clearance Invariant
          - code [ref=e750]: same_section(WO-26027-019, 22415) and no_time_overlap(0.0, 1.0, 12.520833333333334, 14.083333333333334)
          - paragraph [ref=e751]: No conflict with listed train 22415, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e752]:
          - generic [ref=e753]: Minimum Distance Safety Buffer
          - code [ref=e757]: no_concurrent_exposure(WO-26027-019,22415)
          - paragraph [ref=e758]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e759]:
          - generic [ref=e760]: Passenger Train Clearance Invariant
          - code [ref=e764]: same_section(WO-26027-019, 22435) and no_time_overlap(0.0, 1.0, 21.477272727272727, 23.0)
          - paragraph [ref=e765]: No conflict with listed train 22435, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e766]:
          - generic [ref=e767]: Minimum Distance Safety Buffer
          - code [ref=e771]: no_concurrent_exposure(WO-26027-019,22435)
          - paragraph [ref=e772]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e773]:
          - generic [ref=e774]: Passenger Train Clearance Invariant
          - code [ref=e778]: same_section(WO-26027-019, 22449) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)
          - paragraph [ref=e779]: No conflict with listed train 22449, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e780]:
          - generic [ref=e781]: Minimum Distance Safety Buffer
          - code [ref=e785]: no_concurrent_exposure(WO-26027-019,22449)
          - paragraph [ref=e786]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e787]:
          - generic [ref=e788]: Passenger Train Clearance Invariant
          - code [ref=e792]: same_section(WO-26027-019, 22581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)
          - paragraph [ref=e793]: No conflict with listed train 22581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e794]:
          - generic [ref=e795]: Minimum Distance Safety Buffer
          - code [ref=e799]: no_concurrent_exposure(WO-26027-019,22581)
          - paragraph [ref=e800]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e801]:
          - generic [ref=e802]: Passenger Train Clearance Invariant
          - code [ref=e806]: same_section(WO-26027-019, 22811) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)
          - paragraph [ref=e807]: No conflict with listed train 22811, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e808]:
          - generic [ref=e809]: Minimum Distance Safety Buffer
          - code [ref=e813]: no_concurrent_exposure(WO-26027-019,22811)
          - paragraph [ref=e814]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e815]:
          - generic [ref=e816]: Passenger Train Clearance Invariant
          - code [ref=e820]: same_section(WO-26027-019, 22823) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)
          - paragraph [ref=e821]: No conflict with listed train 22823, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e822]:
          - generic [ref=e823]: Minimum Distance Safety Buffer
          - code [ref=e827]: no_concurrent_exposure(WO-26027-019,22823)
          - paragraph [ref=e828]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e829]:
          - generic [ref=e830]: Minimum Distance Safety Buffer
          - code [ref=e834]: timetable_complete_for_exposure(NDLS_CNB_SEC1, UP_LINE)
          - paragraph [ref=e835]: "Exposure to unlisted trains is unknown: no timetable completeness evidence covers this section, track line, and scheduled interval."
        - generic [ref=e836]:
          - generic [ref=e837]: Traction Power Isolation Rule
          - code [ref=e841]: not_traction_work(WO-26027-019) or power_isolated(WO-26027-019)
          - paragraph [ref=e842]: Work WO-26027-019 is not traction work; the traction isolation rule does not apply.
        - generic [ref=e843]:
          - generic [ref=e844]: Scheduled Block Time Validity
          - code [ref=e848]: 0 <= 0.0 < 1.0 <= 24
          - paragraph [ref=e849]: Work WO-26027-021 has a valid scheduled time interval.
        - generic [ref=e850]:
          - generic [ref=e851]: Passenger Train Clearance Invariant
          - code [ref=e855]: same_section(WO-26027-021, 12003) and no_time_overlap(0.0, 1.0, 20.53030303030303, 22.416666666666668)
          - paragraph [ref=e856]: No conflict with listed train 12003, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e857]:
          - generic [ref=e858]: Minimum Distance Safety Buffer
          - code [ref=e862]: no_concurrent_exposure(WO-26027-021,12003)
          - paragraph [ref=e863]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e864]:
          - generic [ref=e865]: Passenger Train Clearance Invariant
          - code [ref=e869]: same_section(WO-26027-021, 12033) and no_time_overlap(0.0, 1.0, 9.515151515151516, 11.333333333333334)
          - paragraph [ref=e870]: No conflict with listed train 12033, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e871]:
          - generic [ref=e872]: Minimum Distance Safety Buffer
          - code [ref=e876]: no_concurrent_exposure(WO-26027-021,12033)
          - paragraph [ref=e877]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e878]:
          - generic [ref=e879]: Passenger Train Clearance Invariant
          - code [ref=e883]: same_section(WO-26027-021, 12259) and no_time_overlap(0.0, 1.0, 9.125, 11.0)
          - paragraph [ref=e884]: No conflict with listed train 12259, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e885]:
          - generic [ref=e886]: Minimum Distance Safety Buffer
          - code [ref=e890]: no_concurrent_exposure(WO-26027-021,12259)
          - paragraph [ref=e891]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e892]:
          - generic [ref=e893]: Passenger Train Clearance Invariant
          - code [ref=e897]: same_section(WO-26027-021, 12273) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)
          - paragraph [ref=e898]: No conflict with listed train 12273, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e899]:
          - generic [ref=e900]: Minimum Distance Safety Buffer
          - code [ref=e904]: no_concurrent_exposure(WO-26027-021,12273)
          - paragraph [ref=e905]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e906]:
          - generic [ref=e907]: Passenger Train Clearance Invariant
          - code [ref=e911]: same_section(WO-26027-021, 12281) and no_time_overlap(0.0, 1.0, 4.706439393939394, 6.666666666666667)
          - paragraph [ref=e912]: No conflict with listed train 12281, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e913]:
          - generic [ref=e914]: Minimum Distance Safety Buffer
          - code [ref=e918]: no_concurrent_exposure(WO-26027-021,12281)
          - paragraph [ref=e919]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e920]:
          - generic [ref=e921]: Passenger Train Clearance Invariant
          - code [ref=e925]: same_section(WO-26027-021, 12301) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)
          - paragraph [ref=e926]: No conflict with listed train 12301, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e927]:
          - generic [ref=e928]: Minimum Distance Safety Buffer
          - code [ref=e932]: no_concurrent_exposure(WO-26027-021,12301)
          - paragraph [ref=e933]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e934]:
          - generic [ref=e935]: Passenger Train Clearance Invariant
          - code [ref=e939]: same_section(WO-26027-021, 12303) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)
          - paragraph [ref=e940]: No conflict with listed train 12303, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e941]:
          - generic [ref=e942]: Minimum Distance Safety Buffer
          - code [ref=e946]: no_concurrent_exposure(WO-26027-021,12303)
          - paragraph [ref=e947]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e948]:
          - generic [ref=e949]: Passenger Train Clearance Invariant
          - code [ref=e953]: same_section(WO-26027-021, 12305) and no_time_overlap(0.0, 1.0, 8.293560606060606, 10.083333333333334)
          - paragraph [ref=e954]: No conflict with listed train 12305, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e955]:
          - generic [ref=e956]: Minimum Distance Safety Buffer
          - code [ref=e960]: no_concurrent_exposure(WO-26027-021,12305)
          - paragraph [ref=e961]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e962]:
          - generic [ref=e963]: Passenger Train Clearance Invariant
          - code [ref=e967]: same_section(WO-26027-021, 12309) and no_time_overlap(0.0, 1.0, 5.8484848484848495, 7.666666666666668)
          - paragraph [ref=e968]: No conflict with listed train 12309, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e969]:
          - generic [ref=e970]: Minimum Distance Safety Buffer
          - code [ref=e974]: no_concurrent_exposure(WO-26027-021,12309)
          - paragraph [ref=e975]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e976]:
          - generic [ref=e977]: Passenger Train Clearance Invariant
          - code [ref=e981]: same_section(WO-26027-021, 12313) and no_time_overlap(0.0, 1.0, 8.958333333333334, 10.833333333333334)
          - paragraph [ref=e982]: No conflict with listed train 12313, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e983]:
          - generic [ref=e984]: Minimum Distance Safety Buffer
          - code [ref=e988]: no_concurrent_exposure(WO-26027-021,12313)
          - paragraph [ref=e989]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e990]:
          - generic [ref=e991]: Passenger Train Clearance Invariant
          - code [ref=e995]: same_section(WO-26027-021, 12349) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)
          - paragraph [ref=e996]: No conflict with listed train 12349, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e997]:
          - generic [ref=e998]: Minimum Distance Safety Buffer
          - code [ref=e1002]: no_concurrent_exposure(WO-26027-021,12349)
          - paragraph [ref=e1003]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1004]:
          - generic [ref=e1005]: Passenger Train Clearance Invariant
          - code [ref=e1009]: same_section(WO-26027-021, 12381) and no_time_overlap(0.0, 1.0, 4.049242424242424, 6.083333333333333)
          - paragraph [ref=e1010]: No conflict with listed train 12381, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1011]:
          - generic [ref=e1012]: Minimum Distance Safety Buffer
          - code [ref=e1016]: no_concurrent_exposure(WO-26027-021,12381)
          - paragraph [ref=e1017]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1018]:
          - generic [ref=e1019]: Passenger Train Clearance Invariant
          - code [ref=e1023]: same_section(WO-26027-021, 12393) and no_time_overlap(0.0, 1.0, 6.070075757575758, 7.916666666666667)
          - paragraph [ref=e1024]: No conflict with listed train 12393, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1025]:
          - generic [ref=e1026]: Minimum Distance Safety Buffer
          - code [ref=e1030]: no_concurrent_exposure(WO-26027-021,12393)
          - paragraph [ref=e1031]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1032]:
          - generic [ref=e1033]: Passenger Train Clearance Invariant
          - code [ref=e1037]: same_section(WO-26027-021, 12397) and no_time_overlap(0.0, 1.0, 2.121212121212121, 4.166666666666668)
          - paragraph [ref=e1038]: No conflict with listed train 12397, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1039]:
          - generic [ref=e1040]: Minimum Distance Safety Buffer
          - code [ref=e1044]: no_concurrent_exposure(WO-26027-021,12397)
          - paragraph [ref=e1045]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1046]:
          - generic [ref=e1047]: Passenger Train Clearance Invariant
          - code [ref=e1051]: same_section(WO-26027-021, 12417) and no_time_overlap(0.0, 1.0, 4.784090909090909, 7.0)
          - paragraph [ref=e1052]: No conflict with listed train 12417, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1053]:
          - generic [ref=e1054]: Minimum Distance Safety Buffer
          - code [ref=e1058]: no_concurrent_exposure(WO-26027-021,12417)
          - paragraph [ref=e1059]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1060]:
          - generic [ref=e1061]: Passenger Train Clearance Invariant
          - code [ref=e1065]: same_section(WO-26027-021, 12419) and no_time_overlap(0.0, 1.0, 12.397727272727273, 15.0)
          - paragraph [ref=e1066]: No conflict with listed train 12419, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1067]:
          - generic [ref=e1068]: Minimum Distance Safety Buffer
          - code [ref=e1072]: no_concurrent_exposure(WO-26027-021,12419)
          - paragraph [ref=e1073]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1074]:
          - generic [ref=e1075]: Passenger Train Clearance Invariant
          - code [ref=e1079]: same_section(WO-26027-021, 12423) and no_time_overlap(0.0, 1.0, 8.625, 10.5)
          - paragraph [ref=e1080]: No conflict with listed train 12423, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1081]:
          - generic [ref=e1082]: Minimum Distance Safety Buffer
          - code [ref=e1086]: no_concurrent_exposure(WO-26027-021,12423)
          - paragraph [ref=e1087]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1088]:
          - generic [ref=e1089]: Passenger Train Clearance Invariant
          - code [ref=e1093]: same_section(WO-26027-021, 12451) and no_time_overlap(0.0, 1.0, 3.871212121212121, 5.916666666666668)
          - paragraph [ref=e1094]: No conflict with listed train 12451, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1095]:
          - generic [ref=e1096]: Minimum Distance Safety Buffer
          - code [ref=e1100]: no_concurrent_exposure(WO-26027-021,12451)
          - paragraph [ref=e1101]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1102]:
          - generic [ref=e1103]: Passenger Train Clearance Invariant
          - code [ref=e1107]: same_section(WO-26027-021, 12453) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)
          - paragraph [ref=e1108]: No conflict with listed train 12453, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1109]:
          - generic [ref=e1110]: Minimum Distance Safety Buffer
          - code [ref=e1114]: no_concurrent_exposure(WO-26027-021,12453)
          - paragraph [ref=e1115]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1116]:
          - generic [ref=e1117]: Passenger Train Clearance Invariant
          - code [ref=e1121]: same_section(WO-26027-021, 12553) and no_time_overlap(0.0, 1.0, 4.1439393939393945, 6.416666666666668)
          - paragraph [ref=e1122]: No conflict with listed train 12553, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1123]:
          - generic [ref=e1124]: Minimum Distance Safety Buffer
          - code [ref=e1128]: no_concurrent_exposure(WO-26027-021,12553)
          - paragraph [ref=e1129]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1130]:
          - generic [ref=e1131]: Passenger Train Clearance Invariant
          - code [ref=e1135]: same_section(WO-26027-021, 12555) and no_time_overlap(0.0, 1.0, 3.25, 5.25)
          - paragraph [ref=e1136]: No conflict with listed train 12555, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1137]:
          - generic [ref=e1138]: Minimum Distance Safety Buffer
          - code [ref=e1142]: no_concurrent_exposure(WO-26027-021,12555)
          - paragraph [ref=e1143]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1144]:
          - generic [ref=e1145]: Passenger Train Clearance Invariant
          - code [ref=e1149]: same_section(WO-26027-021, 12559) and no_time_overlap(0.0, 1.0, 6.568181818181818, 8.5)
          - paragraph [ref=e1150]: No conflict with listed train 12559, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1151]:
          - generic [ref=e1152]: Minimum Distance Safety Buffer
          - code [ref=e1156]: no_concurrent_exposure(WO-26027-021,12559)
          - paragraph [ref=e1157]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1158]:
          - generic [ref=e1159]: Passenger Train Clearance Invariant
          - code [ref=e1163]: same_section(WO-26027-021, 12561) and no_time_overlap(0.0, 1.0, 13.676136363636363, 15.75)
          - paragraph [ref=e1164]: No conflict with listed train 12561, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1165]:
          - generic [ref=e1166]: Minimum Distance Safety Buffer
          - code [ref=e1170]: no_concurrent_exposure(WO-26027-021,12561)
          - paragraph [ref=e1171]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1172]:
          - generic [ref=e1173]: Passenger Train Clearance Invariant
          - code [ref=e1177]: same_section(WO-26027-021, 12565) and no_time_overlap(0.0, 1.0, 2.924242424242422, 5.083333333333332)
          - paragraph [ref=e1178]: No conflict with listed train 12565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1179]:
          - generic [ref=e1180]: Minimum Distance Safety Buffer
          - code [ref=e1184]: no_concurrent_exposure(WO-26027-021,12565)
          - paragraph [ref=e1185]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1186]:
          - generic [ref=e1187]: Passenger Train Clearance Invariant
          - code [ref=e1191]: same_section(WO-26027-021, 12581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)
          - paragraph [ref=e1192]: No conflict with listed train 12581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1193]:
          - generic [ref=e1194]: Minimum Distance Safety Buffer
          - code [ref=e1198]: no_concurrent_exposure(WO-26027-021,12581)
          - paragraph [ref=e1199]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1200]:
          - generic [ref=e1201]: Passenger Train Clearance Invariant
          - code [ref=e1205]: same_section(WO-26027-021, 12877) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)
          - paragraph [ref=e1206]: No conflict with listed train 12877, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1207]:
          - generic [ref=e1208]: Minimum Distance Safety Buffer
          - code [ref=e1212]: no_concurrent_exposure(WO-26027-021,12877)
          - paragraph [ref=e1213]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1214]:
          - generic [ref=e1215]: Passenger Train Clearance Invariant
          - code [ref=e1219]: same_section(WO-26027-021, 13007) and no_time_overlap(0.0, 1.0, 15.916666666666668, 19.666666666666668)
          - paragraph [ref=e1220]: No conflict with listed train 13007, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1221]:
          - generic [ref=e1222]: Minimum Distance Safety Buffer
          - code [ref=e1226]: no_concurrent_exposure(WO-26027-021,13007)
          - paragraph [ref=e1227]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1228]:
          - generic [ref=e1229]: Passenger Train Clearance Invariant
          - code [ref=e1233]: same_section(WO-26027-021, 14037) and no_time_overlap(0.0, 1.0, 10.674242424242426, 12.833333333333334)
          - paragraph [ref=e1234]: No conflict with listed train 14037, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1235]:
          - generic [ref=e1236]: Minimum Distance Safety Buffer
          - code [ref=e1240]: no_concurrent_exposure(WO-26027-021,14037)
          - paragraph [ref=e1241]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1242]:
          - generic [ref=e1243]: Passenger Train Clearance Invariant
          - code [ref=e1247]: same_section(WO-26027-021, 14619) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)
          - paragraph [ref=e1248]: No conflict with listed train 14619, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1249]:
          - generic [ref=e1250]: Minimum Distance Safety Buffer
          - code [ref=e1254]: no_concurrent_exposure(WO-26027-021,14619)
          - paragraph [ref=e1255]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1256]:
          - generic [ref=e1257]: Passenger Train Clearance Invariant
          - code [ref=e1261]: same_section(WO-26027-021, 15565) and no_time_overlap(0.0, 1.0, 4.198863636363637, 6.5)
          - paragraph [ref=e1262]: No conflict with listed train 15565, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1263]:
          - generic [ref=e1264]: Minimum Distance Safety Buffer
          - code [ref=e1268]: no_concurrent_exposure(WO-26027-021,15565)
          - paragraph [ref=e1269]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1270]:
          - generic [ref=e1271]: Passenger Train Clearance Invariant
          - code [ref=e1275]: same_section(WO-26027-021, 20407) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)
          - paragraph [ref=e1276]: No conflict with listed train 20407, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1277]:
          - generic [ref=e1278]: Minimum Distance Safety Buffer
          - code [ref=e1282]: no_concurrent_exposure(WO-26027-021,20407)
          - paragraph [ref=e1283]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1284]:
          - generic [ref=e1285]: Passenger Train Clearance Invariant
          - code [ref=e1289]: same_section(WO-26027-021, 20801) and no_time_overlap(0.0, 1.0, 9.301136363636363, 12.0)
          - paragraph [ref=e1290]: No conflict with listed train 20801, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1291]:
          - generic [ref=e1292]: Minimum Distance Safety Buffer
          - code [ref=e1296]: no_concurrent_exposure(WO-26027-021,20801)
          - paragraph [ref=e1297]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1298]:
          - generic [ref=e1299]: Passenger Train Clearance Invariant
          - code [ref=e1303]: same_section(WO-26027-021, 20817) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)
          - paragraph [ref=e1304]: No conflict with listed train 20817, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1305]:
          - generic [ref=e1306]: Minimum Distance Safety Buffer
          - code [ref=e1310]: no_concurrent_exposure(WO-26027-021,20817)
          - paragraph [ref=e1311]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1312]:
          - generic [ref=e1313]: Passenger Train Clearance Invariant
          - code [ref=e1317]: same_section(WO-26027-021, 20839) and no_time_overlap(0.0, 1.0, 9.291666666666666, 11.166666666666666)
          - paragraph [ref=e1318]: No conflict with listed train 20839, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1319]:
          - generic [ref=e1320]: Minimum Distance Safety Buffer
          - code [ref=e1324]: no_concurrent_exposure(WO-26027-021,20839)
          - paragraph [ref=e1325]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1326]:
          - generic [ref=e1327]: Passenger Train Clearance Invariant
          - code [ref=e1331]: same_section(WO-26027-021, 22361) and no_time_overlap(0.0, 1.0, 10.212121212121211, 13.166666666666666)
          - paragraph [ref=e1332]: No conflict with listed train 22361, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1333]:
          - generic [ref=e1334]: Minimum Distance Safety Buffer
          - code [ref=e1338]: no_concurrent_exposure(WO-26027-021,22361)
          - paragraph [ref=e1339]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1340]:
          - generic [ref=e1341]: Passenger Train Clearance Invariant
          - code [ref=e1345]: same_section(WO-26027-021, 22415) and no_time_overlap(0.0, 1.0, 12.520833333333334, 14.083333333333334)
          - paragraph [ref=e1346]: No conflict with listed train 22415, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1347]:
          - generic [ref=e1348]: Minimum Distance Safety Buffer
          - code [ref=e1352]: no_concurrent_exposure(WO-26027-021,22415)
          - paragraph [ref=e1353]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1354]:
          - generic [ref=e1355]: Passenger Train Clearance Invariant
          - code [ref=e1359]: same_section(WO-26027-021, 22435) and no_time_overlap(0.0, 1.0, 21.477272727272727, 23.0)
          - paragraph [ref=e1360]: No conflict with listed train 22435, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1361]:
          - generic [ref=e1362]: Minimum Distance Safety Buffer
          - code [ref=e1366]: no_concurrent_exposure(WO-26027-021,22435)
          - paragraph [ref=e1367]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1368]:
          - generic [ref=e1369]: Passenger Train Clearance Invariant
          - code [ref=e1373]: same_section(WO-26027-021, 22449) and no_time_overlap(0.0, 1.0, 10.702651515151516, 12.833333333333334)
          - paragraph [ref=e1374]: No conflict with listed train 22449, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1375]:
          - generic [ref=e1376]: Minimum Distance Safety Buffer
          - code [ref=e1380]: no_concurrent_exposure(WO-26027-021,22449)
          - paragraph [ref=e1381]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1382]:
          - generic [ref=e1383]: Passenger Train Clearance Invariant
          - code [ref=e1387]: same_section(WO-26027-021, 22581) and no_time_overlap(0.0, 1.0, 7.761363636363637, 9.75)
          - paragraph [ref=e1388]: No conflict with listed train 22581, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1389]:
          - generic [ref=e1390]: Minimum Distance Safety Buffer
          - code [ref=e1394]: no_concurrent_exposure(WO-26027-021,22581)
          - paragraph [ref=e1395]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1396]:
          - generic [ref=e1397]: Passenger Train Clearance Invariant
          - code [ref=e1401]: same_section(WO-26027-021, 22811) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)
          - paragraph [ref=e1402]: No conflict with listed train 22811, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1403]:
          - generic [ref=e1404]: Minimum Distance Safety Buffer
          - code [ref=e1408]: no_concurrent_exposure(WO-26027-021,22811)
          - paragraph [ref=e1409]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1410]:
          - generic [ref=e1411]: Passenger Train Clearance Invariant
          - code [ref=e1415]: same_section(WO-26027-021, 22823) and no_time_overlap(0.0, 1.0, 8.12689393939394, 9.916666666666666)
          - paragraph [ref=e1416]: No conflict with listed train 22823, but timetable completeness is not confirmed for this section, track line, and interval; clearance is unevaluated.
        - generic [ref=e1417]:
          - generic [ref=e1418]: Minimum Distance Safety Buffer
          - code [ref=e1422]: no_concurrent_exposure(WO-26027-021,22823)
          - paragraph [ref=e1423]: The work and train windows do not overlap, so no simultaneous exposure requires a spatial buffer check for this known train.
        - generic [ref=e1424]:
          - generic [ref=e1425]: Minimum Distance Safety Buffer
          - code [ref=e1429]: timetable_complete_for_exposure(NDLS_CNB_SEC1, UP_LINE)
          - paragraph [ref=e1430]: "Exposure to unlisted trains is unknown: no timetable completeness evidence covers this section, track line, and scheduled interval."
        - generic [ref=e1431]:
          - generic [ref=e1432]: Traction Power Isolation Rule
          - code [ref=e1436]: not_traction_work(WO-26027-021) or power_isolated(WO-26027-021)
          - paragraph [ref=e1437]: Work WO-26027-021 is not traction work; the traction isolation rule does not apply.
  - button "Open Next.js Dev Tools" [ref=e1443] [cursor=pointer]
  - alert [ref=e1447]
```

# Test source

```ts
  132 |   });
  133 | 
  134 |   test("B05 displayed metrics correspond to the API response", async ({ page }, info) => {
  135 |     await openApp(page);
  136 |     const { json } = await generateSchedule(page);
  137 |     const m = json.metrics;
  138 |     const text = await bodyText(page);
  139 |     note(info, `API metrics: ${JSON.stringify(m)}; status=${json.status}; solver_outcome=${json.solver_outcome}`);
  140 |     expect(text).toContain(`${m.scheduled_requests}/${m.total_requests} blocks scheduled`);
  141 |     expect(text).toContain(`${Number(m.search_space_pruned_pct).toFixed(1)}%`);
  142 |     expect(text).toContain(`${m.solver_execution_time_sec.toFixed(2)} s`);
  143 |     expect(text).toContain(`${m.co_location_merges_count} co-location merges`);
  144 |     expect(m.scheduled_requests + json.unscheduled_work_ids.length).toBe(m.total_requests);
  145 |   });
  146 | 
  147 |   test("B06 safety-rule compliance is not shown as verified when the API says it is unverified", async ({ page }, info) => {
  148 |     await openApp(page);
  149 |     const { json } = await generateSchedule(page);
  150 |     const card = page.locator("div").filter({ hasText: /^Safety Rule Compliance/ }).last();
  151 |     const cardText = (await card.innerText()).replace(/\n/g, " ");
  152 |     note(info, `API fol_rule_compliance_pct=${json.metrics.fol_rule_compliance_pct}, status=${json.status}; card="${cardText}"`);
  153 |     await shot(page, info, "G-errors-usability", "B06_safety-compliance-card", { fullPage: false });
  154 |     if (json.metrics.fol_rule_compliance_pct === null) {
  155 |       expect(cardText).not.toMatch(/\d+(\.\d+)?\s*%/);
  156 |       await expect(page.getByText(/status: safety_unverified/)).toBeVisible();
  157 |     }
  158 |   });
  159 | 
  160 |   test("B07 scheduled and unscheduled accounting is consistent with Gantt bars", async ({ page }, info) => {
  161 |     await openApp(page);
  162 |     const { json } = await generateSchedule(page);
  163 |     const barIds = (await woBars(page).allInnerTexts()).map((t) => t.replace(/\s+/g, " ").match(/WO-\S+/)?.[0]);
  164 |     const apiIds = json.schedule.map((s: { work_id: string }) => s.work_id).sort();
  165 |     expect([...new Set(barIds)].sort()).toEqual(apiIds);
  166 |     note(info, `bars=${barIds.length}, scheduled=${apiIds.length}, unscheduled=${json.unscheduled_work_ids.length}`);
  167 |     if (json.unscheduled_work_ids.length === 0) {
  168 |       const text = await bodyText(page);
  169 |       note(info, `unscheduled section visible in production UI: ${/unscheduled/i.test(text)}`);
  170 |     }
  171 |   });
  172 | 
  173 |   test("B08 other corridor schedules and renders its own sections", async ({ page }, info) => {
  174 |     await openApp(page);
  175 |     await page.getByLabel("Corridor").selectOption({ index: 1 });
  176 |     const { resp, json } = await generateSchedule(page);
  177 |     expect(resp.status()).toBe(200);
  178 |     await expect(page.getByText("HWH_PURI_SEC1").first()).toBeVisible();
  179 |     note(info, `HWH_PURI scheduled=${json.metrics.scheduled_requests}/${json.metrics.total_requests}`);
  180 |     await shot(page, info, "B-scheduling", "B08_second-corridor-schedule", { fullPage: false });
  181 |   });
  182 | 
  183 |   test("B09 production work-order subset is honoured, then restored (state-restoring test)", async ({ page }, info) => {
  184 |     await openApp(page);
  185 |     await page.getByRole("button", { name: /^Work Orders/ }).click();
  186 |     const dlg = page.locator("aside").filter({ hasText: "Work Order Manager" });
  187 |     try {
  188 |       const first = dlg.getByRole("checkbox").first();
  189 |       await first.uncheck();
  190 |       const apply = dlg.getByRole("button", { name: /Apply \d+ enabled/ });
  191 |       await expect(apply).toContainText("29");
  192 |       await apply.click();
  193 |       await dlg.getByRole("button", { name: "Close" }).click();
  194 |       const { json } = await generateSchedule(page);
  195 |       note(info, `after disabling 1 work order: total_requests=${json.metrics.total_requests}`);
  196 |       expect(json.metrics.total_requests).toBe(29);
  197 |     } finally {
  198 |       // Restore the shared in-memory backend state regardless of outcome.
  199 |       const open = await page.locator("aside").filter({ hasText: "Work Order Manager" }).count();
  200 |       if (!open) await page.getByRole("button", { name: /^Work Orders/ }).click();
  201 |       await page.locator("aside").filter({ hasText: "Work Order Manager" }).getByRole("button", { name: "Reset to synthetic" }).click();
  202 |       await page.waitForTimeout(800);
  203 |       const wos = await (await page.request.get(`${API}/api/data/work-orders`)).json();
  204 |       expect(wos.length, "backend work orders restored to synthetic set").toBe(30);
  205 |     }
  206 |   });
  207 | 
  208 |   test("B10 empty selection cannot be applied (empty work-order set)", async ({ page }, info) => {
  209 |     await openApp(page);
  210 |     await page.getByRole("button", { name: /^Work Orders/ }).click();
  211 |     const dlg = page.locator("aside").filter({ hasText: "Work Order Manager" });
  212 |     const boxes = dlg.getByRole("checkbox");
  213 |     const n = await boxes.count();
  214 |     for (let i = 0; i < n; i++) await boxes.nth(i).uncheck();
  215 |     await shot(page, info, "G-errors-usability", "B10_all-work-orders-disabled", { fullPage: false });
  216 |     await expect(dlg.getByRole("button", { name: /Apply 0 enabled/ })).toBeDisabled();
  217 |   });
  218 | });
  219 | 
  220 | test.describe("B (cont.). Solver outcome communication", () => {
  221 |   test("B11 production UI communicates an unschedulable/partial outcome and lists unscheduled work orders", async ({ page }, info) => {
  222 |     await openApp(page);
  223 |     await page.getByLabel("Horizon (hrs)").fill("1");
  224 |     const { json } = await generateSchedule(page);
  225 |     await page.waitForTimeout(600);
  226 |     const text = await bodyText(page);
  227 |     await shot(page, info, "B-scheduling", "B11_partial-schedule-outcome", { fullPage: true });
  228 |     note(info, `API: solver_outcome=${json.solver_outcome}, status=${json.status}, unscheduled=${json.unscheduled_work_ids.length}/${json.metrics.total_requests}`);
  229 |     expect(json.unscheduled_work_ids.length, "precondition: horizon=1 should leave work orders unscheduled").toBeGreaterThan(0);
  230 |     expect.soft(text, "solver outcome shown").toMatch(new RegExp(json.solver_outcome, "i"));
  231 |     expect.soft(text, "unscheduled work-order IDs shown").toContain(json.unscheduled_work_ids[0]);
> 232 |     expect.soft(text, "unscheduled count / warning shown").toMatch(/unscheduled|not scheduled|could not be scheduled/i);
      |                                                            ^ Error: unscheduled count / warning shown
  233 |   });
  234 | });
  235 | 
  236 | // ───────────────────────── C. Scenario management ─────────────────────────
  237 | test.describe("C. Scenario management", () => {
  238 |   test("C01 create a scenario", async ({ page }, info) => {
  239 |     await openApp(page);
  240 |     await shot(page, info, "C-scenarios", "C01_scenario-management-empty", { fullPage: false });
  241 |     await createScenario(page, "Audit scenario A", ["NDLS_CNB_SEC1"]);
  242 |     await expect(saveBtn(page)).toContainText("*"); // unsaved-changes marker
  243 |     await shot(page, info, "C-scenarios", "C01_scenario-created-draft", { fullPage: false });
  244 |   });
  245 | 
  246 |   test("C02 creation validation: no name / no section", async ({ page }, info) => {
  247 |     await openApp(page);
  248 |     await page.getByRole("button", { name: "Create", exact: true }).click();
  249 |     await shot(page, info, "G-errors-usability", "C02_create-without-input", { fullPage: false });
  250 |     await expect(page.getByText(/Select at least one route section|name/i).first()).toBeVisible();
  251 |     await page.getByPlaceholder("My maintenance scenario").fill("   ");
  252 |     await creationSections(page).getByLabel("NDLS_CNB_SEC1").check();
  253 |     await page.getByRole("button", { name: "Create", exact: true }).click();
  254 |     const opts = await scenarioSelect(page).count();
  255 |     note(info, `whitespace-only name: scenario selector present = ${opts > 0}`);
  256 |   });
  257 | 
  258 |   test("C03 save a scenario writes versioned data to localStorage", async ({ page }, info) => {
  259 |     await openApp(page);
  260 |     await createScenario(page, "Audit scenario A", ["NDLS_CNB_SEC1"]);
  261 |     await saveBtn(page).click();
  262 |     const raw = await page.evaluate((k) => localStorage.getItem(k), STORAGE_KEY);
  263 |     expect(raw).not.toBeNull();
  264 |     const data = JSON.parse(raw!);
  265 |     note(info, `stored keys: ${Object.keys(data)}`);
  266 |     expect(data.schema_version).toBe(1);
  267 |     expect(JSON.stringify(data)).toContain("Audit scenario A");
  268 |     await expect(saveBtn(page)).not.toContainText("*");
  269 |     await shot(page, info, "C-scenarios", "C03_scenario-saved", { fullPage: false });
  270 |   });
  271 | 
  272 |   test("C04 saved scenario persists after reload", async ({ page }, info) => {
  273 |     await openApp(page);
  274 |     await createScenario(page, "Persist me", ["NDLS_CNB_SEC1"]);
  275 |     await addWorkOrders(page, [BASIC_ORDERS[0]]);
  276 |     await saveBtn(page).click();
  277 |     await page.reload();
  278 |     await expect(page.getByText("API online")).toBeVisible();
  279 |     const autoLoaded = (await scenarioSelect(page).count()) > 0;
  280 |     note(info, `scenario automatically loaded after reload: ${autoLoaded}`);
  281 |     if (!autoLoaded) await page.getByRole("button", { name: "Reload saved" }).click();
  282 |     await expect(scenarioSelect(page)).toContainText("Persist me");
  283 |     await expect(page.getByRole("button", { name: /Manage work orders \(1\)/ })).toBeVisible();
  284 |     await shot(page, info, "C-scenarios", "C04_scenario-after-reload", { fullPage: false });
  285 |   });
  286 | 
  287 |   test("C05 unsaved draft is discarded on reload without warning", async ({ page }, info) => {
  288 |     await openApp(page);
  289 |     await createScenario(page, "Unsaved draft", ["NDLS_CNB_SEC1"]);
  290 |     let beforeUnload = false;
  291 |     page.on("dialog", async (d) => {
  292 |       if (d.type() === "beforeunload") beforeUnload = true;
  293 |       await d.dismiss();
  294 |     });
  295 |     await page.reload();
  296 |     const stillThere = (await scenarioSelect(page).count()) > 0;
  297 |     note(info, `draft survived reload=${stillThere}; beforeunload warning shown=${beforeUnload}`);
  298 |     await shot(page, info, "G-errors-usability", "C05_draft-lost-after-reload", { fullPage: false });
  299 |     // Documented as designed behaviour ("It will remain a draft until saved"); the missing warning is a usability observation.
  300 |     expect(stillThere).toBe(false);
  301 |   });
  302 | 
  303 |   test("C06 duplicate a scenario", async ({ page }, info) => {
  304 |     await openApp(page);
  305 |     await createScenario(page, "Dup source", ["NDLS_CNB_SEC1"]);
  306 |     await page.getByRole("button", { name: "Duplicate" }).click();
  307 |     const opts = await scenarioSelect(page).locator("option").allTextContents();
  308 |     note(info, `options after duplicate: ${JSON.stringify(opts)}`);
  309 |     expect(opts.length).toBe(2);
  310 |     expect(new Set(opts).size, "duplicate must be distinguishable by name").toBe(2);
  311 |     await shot(page, info, "C-scenarios", "C06_scenario-duplicated", { fullPage: false });
  312 |   });
  313 | 
  314 |   test("C07 rename / edit a scenario", async ({ page }, info) => {
  315 |     await openApp(page);
  316 |     await createScenario(page, "Old name", ["NDLS_CNB_SEC1"]);
  317 |     await page.getByLabel("Scenario name", { exact: true }).fill("Renamed scenario");
  318 |     await page.getByLabel(/Horizon \(hours/).fill("12");
  319 |     await editSections(page).getByLabel("NDLS_CNB_SEC2").check();
  320 |     await page.getByRole("button", { name: "Update scenario settings" }).click();
  321 |     await expect(scenarioSelect(page)).toContainText("Renamed scenario");
  322 |     await saveBtn(page).click();
  323 |     const data = JSON.parse((await page.evaluate((k) => localStorage.getItem(k), STORAGE_KEY))!);
  324 |     const s = JSON.stringify(data);
  325 |     expect(s).toContain("Renamed scenario");
  326 |     expect(s).toContain("NDLS_CNB_SEC2");
  327 |     await shot(page, info, "C-scenarios", "C07_scenario-renamed-edited", { fullPage: false });
  328 |   });
  329 | 
  330 |   test("C08 delete a scenario (and the deletion persists once saved)", async ({ page }, info) => {
  331 |     await openApp(page);
  332 |     await createScenario(page, "To delete", ["NDLS_CNB_SEC1"]);
```