"use client";

import { useState } from "react";
import { Copy, Plus, RefreshCw, Save, Trash2 } from "lucide-react";
import type { RouteInfo, ScenarioSolverConfiguration } from "@/lib/types";
import type { ScenarioRecord } from "@/lib/scenario-storage";
import { getScenarioSectionGroups } from "@/lib/scenario-sections";

interface Props {
  scenarios: ScenarioRecord[];
  routes: RouteInfo[];
  selectedScenarioId: string | null;
  storageStatus: "loading" | "ready" | "error";
  storageError: string | null;
  saveError: string | null;
  dirty: boolean;
  onSelect: (scenarioId: string) => void;
  onCreate: (name: string, sectionIds: string[]) => void;
  onDuplicate: (scenarioId: string, name: string) => void;
  onDelete: (scenarioId: string) => void;
  onUpdate: (
    scenarioId: string,
    update: { scenario_name: string; solver_configuration: ScenarioSolverConfiguration },
  ) => void;
  onSave: () => void;
  onReload: () => void;
  onManageWorkOrders: () => void;
}

const fieldClass = "rounded bg-slate-950 p-2 text-sm text-slate-100";

export default function ScenarioManager({
  scenarios,
  routes,
  selectedScenarioId,
  storageStatus,
  storageError,
  saveError,
  dirty,
  onSelect,
  onCreate,
  onDuplicate,
  onDelete,
  onUpdate,
  onSave,
  onReload,
  onManageWorkOrders,
}: Props) {
  const [newName, setNewName] = useState("");
  const [newSections, setNewSections] = useState<string[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  const selected = scenarios.find((scenario) => scenario.scenario_id === selectedScenarioId) ?? null;

  function toggleSection(
    current: string[],
    sectionId: string,
    checked: boolean,
  ): string[] {
    return checked
      ? [...current, sectionId]
      : current.filter((section) => section !== sectionId);
  }

  function create() {
    try {
      if (newSections.length === 0) throw new Error("Select at least one route section.");
      if (!newName.trim()) throw new Error("Scenario name is required.");
      onCreate(newName.trim(), newSections);
      setNewName("");
      setNewSections([]);
      setFormError(null);
    } catch (error) {
      setFormError((error as Error).message);
    }
  }

  const storageReady = storageStatus === "ready";

  return (
    <section className="space-y-4 rounded-xl border border-violet-800/60 bg-slate-900 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">Offline simulation scenarios</h2>
          <p className="mt-1 text-xs text-slate-400">
            Saved scenarios stay in this browser. Running a comparison sends the selected scenario to the experimental API; results are not saved. Do not enter credentials, evidence, or operational railway data. This prototype is not operationally authorized.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onReload}
            disabled={storageStatus === "loading"}
            className="flex items-center gap-1 rounded border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800 disabled:opacity-50"
          >
            <RefreshCw className="h-4 w-4" /> Reload saved
          </button>
          <button
            type="button"
            onClick={onSave}
            disabled={!storageReady || !dirty}
            className="flex items-center gap-1 rounded bg-emerald-700 px-3 py-2 text-sm hover:bg-emerald-600 disabled:opacity-50"
          >
            <Save className="h-4 w-4" /> Save scenarios{dirty ? " *" : ""}
          </button>
        </div>
      </div>

      {storageStatus === "loading" && <p className="text-sm text-slate-400">Loading saved scenarios…</p>}
      {storageError && (
        <div role="alert" className="rounded border border-rose-800 bg-rose-950/40 p-3 text-sm text-rose-200">
          {storageError} Saving and editing are disabled until the stored data can be read safely.
        </div>
      )}
      {saveError && (
        <div role="alert" className="rounded border border-amber-800 bg-amber-950/40 p-3 text-sm text-amber-200">
          {saveError}
        </div>
      )}

      {storageReady && (
        <>
          <div className="grid gap-3 md:grid-cols-[minmax(12rem,1fr)_minmax(12rem,2fr)_auto]">
            <label className="flex flex-col gap-1 text-xs text-slate-400">
              New scenario name
              <input
                className={fieldClass}
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
                placeholder="My maintenance scenario"
              />
            </label>
            <SectionSelection
              label="Scenario sections"
              groups={getScenarioSectionGroups(routes)}
              selected={newSections}
              onChange={(sectionId, checked) => setNewSections((current) =>
                toggleSection(current, sectionId, checked),
              )}
              emptyMessage="Load route information to choose valid section IDs."
            />
            <button type="button" onClick={create} className="mt-auto flex items-center justify-center gap-1 rounded bg-cyan-700 px-3 py-2 text-sm hover:bg-cyan-600">
              <Plus className="h-4 w-4" /> Create
            </button>
          </div>

          {scenarios.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-700 p-5 text-center">
              <p className="text-sm text-slate-300">No saved scenarios yet.</p>
              <p className="mt-1 text-xs text-slate-500">Create an offline scenario above. It will remain a draft until saved.</p>
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-[minmax(14rem,1fr)_minmax(18rem,2fr)]">
              <div className="space-y-2">
                <label className="flex flex-col gap-1 text-xs text-slate-400">
                  Scenario
                  <select
                    className={fieldClass}
                    value={selectedScenarioId ?? ""}
                    onChange={(event) => onSelect(event.target.value)}
                  >
                    {scenarios.map((scenario) => (
                      <option key={scenario.scenario_id} value={scenario.scenario_id}>
                        {scenario.scenario_name}
                      </option>
                    ))}
                  </select>
                </label>
                {selected && (
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => onDuplicate(selected.scenario_id, `${selected.scenario_name} copy`)}
                      className="flex items-center gap-1 rounded border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800"
                    >
                      <Copy className="h-4 w-4" /> Duplicate
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (window.confirm(`Delete "${selected.scenario_name}" from this unsaved draft?`)) {
                          onDelete(selected.scenario_id);
                        }
                      }}
                      className="flex items-center gap-1 rounded border border-rose-900 px-3 py-2 text-sm text-rose-300 hover:bg-rose-950"
                    >
                      <Trash2 className="h-4 w-4" /> Delete
                    </button>
                  </div>
                )}
              </div>

              {selected && (
                <ScenarioSettings
                  key={`${selected.scenario_id}|${selected.scenario_name}|${selected.solver_configuration.section_ids.join(",")}|${selected.solver_configuration.time_horizon_hrs}`}
                  scenario={selected}
                  routes={routes}
                  onUpdate={onUpdate}
                  onManageWorkOrders={onManageWorkOrders}
                />
              )}
            </div>
          )}
        </>
      )}
      {formError && <p role="alert" className="text-sm text-rose-300">{formError}</p>}
    </section>
  );
}

function ScenarioSettings({
  scenario,
  routes,
  onUpdate,
  onManageWorkOrders,
}: {
  scenario: ScenarioRecord;
  routes: RouteInfo[];
  onUpdate: Props["onUpdate"];
  onManageWorkOrders: Props["onManageWorkOrders"];
}) {
  const [nameDraft, setNameDraft] = useState(scenario.scenario_name);
  const [sectionsDraft, setSectionsDraft] = useState(
    scenario.solver_configuration.section_ids,
  );
  const [horizonDraft, setHorizonDraft] = useState(
    String(scenario.solver_configuration.time_horizon_hrs),
  );
  const [error, setError] = useState<string | null>(null);

  function update() {
    try {
      const sections = [...new Set(sectionsDraft)];
      if (sections.length === 0) throw new Error("Select at least one route section.");
      const horizon = Number(horizonDraft);
      if (!Number.isFinite(horizon) || horizon <= 0 || horizon > 24) {
        throw new Error("Horizon must be greater than 0 and no more than 24 hours.");
      }
      if (!Number.isSafeInteger(horizon * 1_000_000)) {
        throw new Error("Horizon precision cannot exceed 0.000001 hours.");
      }
      if (!nameDraft.trim()) throw new Error("Scenario name is required.");
      onUpdate(scenario.scenario_id, {
        scenario_name: nameDraft.trim(),
        solver_configuration: {
          ...scenario.solver_configuration,
          section_ids: sections,
          time_horizon_hrs: horizon,
        },
      });
      setError(null);
    } catch (caught) {
      setError((caught as Error).message);
    }
  }

  return (
    <div className="space-y-3 rounded-lg border border-slate-800 bg-slate-950/40 p-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Scenario name
          <input className={fieldClass} value={nameDraft} onChange={(event) => setNameDraft(event.target.value)} />
        </label>
        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Horizon (hours, maximum 24)
          <input className={fieldClass} type="number" min="0.01" max="24" step="any" value={horizonDraft} onChange={(event) => setHorizonDraft(event.target.value)} />
        </label>
        <SectionSelection
          label="Scenario sections"
          groups={getScenarioSectionGroups(routes, scenario.solver_configuration.section_ids)}
          selected={sectionsDraft}
          onChange={(sectionId, checked) => setSectionsDraft((current) =>
            checked
              ? [...current, sectionId]
              : current.filter((section) => section !== sectionId),
          )}
          emptyMessage="No route sections are currently available."
        />
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={update} className="rounded border border-cyan-800 px-3 py-2 text-sm text-cyan-200 hover:bg-cyan-950">
          Update scenario settings
        </button>
        <button type="button" onClick={onManageWorkOrders} className="rounded border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800">
          Manage work orders ({scenario.work_orders.length})
        </button>
        <span className="text-xs text-slate-500">Model: {scenario.model_version}</span>
      </div>
      {error && <p role="alert" className="text-sm text-rose-300">{error}</p>}
    </div>
  );
}

function SectionSelection({
  label,
  groups,
  selected,
  onChange,
  emptyMessage,
}: {
  label: string;
  groups: ReturnType<typeof getScenarioSectionGroups>;
  selected: string[];
  onChange: (sectionId: string, checked: boolean) => void;
  emptyMessage: string;
}) {
  return (
    <fieldset className="space-y-2 rounded border border-slate-700 p-3 text-xs text-slate-300">
      <legend className="px-1 text-slate-400">{label}</legend>
      {groups.length === 0 ? (
        <p className="text-slate-500">{emptyMessage}</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {groups.map((group) => (
            <div key={group.key} className="space-y-1">
              <p className={group.legacy ? "text-amber-300" : "text-slate-400"}>{group.label}</p>
              {group.legacy && (
                <p className="text-[11px] text-amber-200/80">
                  Retained as stored; it may be rejected by backend validation. Selecting valid sections will not change work-order or train data.
                </p>
              )}
              {group.sectionIds.map((sectionId) => (
                <label key={sectionId} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selected.includes(sectionId)}
                    onChange={(event) => onChange(sectionId, event.target.checked)}
                  />
                  <span className="font-mono">{sectionId}</span>
                </label>
              ))}
            </div>
          ))}
        </div>
      )}
      <p className="text-[11px] text-slate-500">Section IDs come from the backend route list. Existing work orders and train windows must be moved explicitly if you remove their current section.</p>
    </fieldset>
  );
}
