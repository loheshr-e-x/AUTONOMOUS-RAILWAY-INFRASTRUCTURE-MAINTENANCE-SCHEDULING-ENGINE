import type { RouteInfo } from "./types";

export interface ScenarioSectionGroup {
  key: string;
  label: string;
  sectionIds: string[];
  legacy: boolean;
}

export function getScenarioSectionGroups(
  routes: RouteInfo[],
  retainedSectionIds: string[] = [],
): ScenarioSectionGroup[] {
  const knownIds = new Set<string>();
  const groups = routes
    .map((route) => {
      const sectionIds = route.section_ids.filter((sectionId) => {
        if (knownIds.has(sectionId)) return false;
        knownIds.add(sectionId);
        return true;
      });
      return {
        key: route.route_id,
        label: `${route.route_id} · ${route.name}`,
        sectionIds,
        legacy: false,
      };
    })
    .filter((group) => group.sectionIds.length > 0);

  const legacySectionIds = [...new Set(retainedSectionIds)].filter(
    (sectionId) => !knownIds.has(sectionId),
  );
  if (legacySectionIds.length > 0) {
    groups.push({
      key: "existing-unrecognized",
      label: "Existing IDs not found in loaded routes",
      sectionIds: legacySectionIds,
      legacy: true,
    });
  }
  return groups;
}
