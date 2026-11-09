import assert from "node:assert/strict";
import { test } from "node:test";
import { getScenarioSectionGroups } from "../lib/scenario-sections.ts";

const routeFixtures = [
  {
    route_id: "R-A",
    name: "Route A",
    origin: "Origin A",
    destination: "Destination A",
    length_km: 10,
    section_ids: ["A-1", "A-2"],
    train_windows: 2,
  },
  {
    route_id: "R-B",
    name: "Route B",
    origin: "Origin B",
    destination: "Destination B",
    length_km: 20,
    section_ids: ["B-1"],
    train_windows: 1,
  },
];

test("scenario section options are populated from route section IDs", () => {
  const groups = getScenarioSectionGroups(routeFixtures);

  assert.deepEqual(groups, [
    { key: "R-A", label: "R-A · Route A", sectionIds: ["A-1", "A-2"], legacy: false },
    { key: "R-B", label: "R-B · Route B", sectionIds: ["B-1"], legacy: false },
  ]);
});

test("unrecognized existing section IDs remain visible and are not rewritten", () => {
  const retained = ["SIM-A"];
  const groups = getScenarioSectionGroups(routeFixtures, retained);

  assert.deepEqual(groups.at(-1), {
    key: "existing-unrecognized",
    label: "Existing IDs not found in loaded routes",
    sectionIds: ["SIM-A"],
    legacy: true,
  });
  assert.deepEqual(retained, ["SIM-A"]);
});

test("duplicate route section IDs appear only once and known retained IDs are not marked legacy", () => {
  const routes = [
    ...routeFixtures,
    { ...routeFixtures[0], route_id: "R-C", section_ids: ["A-1", "C-1"] },
  ];

  const groups = getScenarioSectionGroups(routes, ["A-1", "SIM-A"]);

  assert.deepEqual(groups.map((group) => group.sectionIds), [
    ["A-1", "A-2"],
    ["B-1"],
    ["C-1"],
    ["SIM-A"],
  ]);
  assert.equal(groups.at(-1)?.legacy, true);
});
