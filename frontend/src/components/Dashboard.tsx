"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Building2, LayoutGrid, Box, Loader2,
  Ruler, Euro, ShieldCheck, GitCompare, FileDown, BarChart3,
  Layers, ListChecks,
} from "lucide-react";
import type {
  Project, Room, Area, Material, HealthResponse,
  QuantityItem, QualityReportData, CostEstimate, Snapshot,
  LPHProgressData,
} from "@/lib/types";
import {
  getHealth, getProjects, getRooms, getAreas, getMaterials,
  getQuantities, getQualityReport, getCostEstimate, getSnapshots,
  getLPHProgress,
} from "@/lib/api";
import { KPICard } from "./KPICard";
import { LiveConnectionCard } from "./LiveConnectionCard";
import { AreaByFloorChart } from "./AreaChart";
import { MaterialDistributionChart } from "./MaterialChart";
import { RoomTable } from "./RoomTable";
import { ReportDownload } from "./ReportDownload";
import { QuantityTable } from "./QuantityTable";
import { QualityReport } from "./QualityReport";
import { CostBreakdown } from "./CostBreakdown";
import { MonitoringDashboard } from "./MonitoringDashboard";
import { DIN277Summary } from "./DIN277Summary";
import { LPHProgressCard } from "./LPHProgressCard";
import { RoomCompletenessMatrix } from "./RoomCompletenessMatrix";
import { AreaEfficiency } from "./AreaEfficiency";
import { FloorOverview } from "./FloorOverview";

type Tab = "overview" | "rooms" | "floors" | "quantities" | "costs" | "quality" | "lph" | "changes" | "reports";

const TABS: { id: Tab; label: string; icon: typeof LayoutGrid }[] = [
  { id: "overview", label: "Übersicht", icon: BarChart3 },
  { id: "rooms", label: "Räume", icon: LayoutGrid },
  { id: "floors", label: "Geschosse", icon: Layers },
  { id: "quantities", label: "Mengen", icon: Ruler },
  { id: "costs", label: "Kosten", icon: Euro },
  { id: "quality", label: "Qualität", icon: ShieldCheck },
  { id: "lph", label: "LPH", icon: ListChecks },
  { id: "changes", label: "Monitoring", icon: GitCompare },
  { id: "reports", label: "Berichte", icon: FileDown },
];

export function Dashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [quantities, setQuantities] = useState<QuantityItem[]>([]);
  const [totalCost, setTotalCost] = useState(0);
  const [qualityReport, setQualityReport] = useState<QualityReportData | null>(null);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [lphProgress, setLphProgress] = useState<LPHProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [projectLoading, setProjectLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  // Initial load
  useEffect(() => {
    async function init() {
      try {
        const [h, p] = await Promise.all([getHealth(), getProjects()]);
        setHealth(h);
        setProjects(p);
        if (p.length > 0) setSelectedId(p[0].id);
      } catch (e) {
        setError("BIM Service nicht erreichbar. Läuft der Service auf Port 8000?");
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Load project data when selection changes
  const loadProjectData = useCallback(async (id: string) => {
    setProjectLoading(true);
    try {
      const [roomData, areaData, matData, qtyData, qualData, costData, snapData, lphData] = await Promise.all([
        getRooms(id),
        getAreas(id),
        getMaterials(id),
        getQuantities(id),
        getQualityReport(id),
        getCostEstimate(id),
        getSnapshots(id),
        getLPHProgress(id).catch(() => null),
      ]);
      setRooms(roomData.rooms);
      setAreas(areaData.areas);
      setMaterials(matData.materials);
      setQuantities(qtyData.quantities);
      setTotalCost(qtyData.total_cost);
      setQualityReport(qualData);
      setCostEstimate(costData);
      setSnapshots(snapData);
      setLphProgress(lphData);
    } catch {
      setError("Fehler beim Laden der Projektdaten");
    } finally {
      setProjectLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId) loadProjectData(selectedId);
  }, [selectedId, loadProjectData]);

  const handleProjectAdded = useCallback((project: Project) => {
    setProjects((prev) => [...prev, project]);
    setSelectedId(project.id);
  }, []);

  const selectedProject = projects.find((p) => p.id === selectedId);

  // KPI calculations
  const totalArea = rooms.reduce((s, r) => s + r.area, 0);
  const nufArea = areas.filter((a) => a.category.startsWith("NUF")).reduce((s, a) => s + a.area, 0);
  const floorCount = new Set(rooms.map((r) => r.floor)).size;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-dcab-blue animate-spin" />
      </div>
    );
  }

  if (error && projects.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-white rounded-lg shadow p-8 max-w-md text-center">
          <p className="text-dcab-navy font-semibold">Verbindungsfehler</p>
          <p className="text-sm text-dcab-gray mt-2">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-dcab-blue text-white rounded-lg text-sm hover:bg-dcab-navy transition-colors"
          >
            Erneut versuchen
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Connection + KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <LiveConnectionCard
          health={health}
          projects={projects}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onProjectAdded={handleProjectAdded}
          onRefresh={() => { if (selectedId) loadProjectData(selectedId); }}
        />
        <KPICard
          title="Räume"
          value={rooms.length}
          subtitle={`${totalArea.toLocaleString("de-DE", { maximumFractionDigits: 0 })} m² Gesamtfläche`}
          icon={LayoutGrid}
          color="navy"
        />
        <KPICard
          title="Nutzfläche (NUF)"
          value={`${nufArea.toLocaleString("de-DE", { maximumFractionDigits: 0 })} m²`}
          subtitle={`${floorCount} Geschosse`}
          icon={Building2}
          color="blue"
        />
        <KPICard
          title="Materialien"
          value={materials.length}
          subtitle={`${new Set(materials.map((m) => m.category)).size} Kategorien`}
          icon={Box}
          color="accent"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto border-b border-gray-200 pb-px">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? "bg-white text-dcab-navy border border-gray-200 border-b-white -mb-px"
                : "text-dcab-gray hover:text-dcab-navy hover:bg-gray-50"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Loading overlay for project switch */}
      {projectLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 text-dcab-blue animate-spin" />
          <span className="ml-2 text-sm text-dcab-gray">Projektdaten laden...</span>
        </div>
      ) : (
        <>
          {activeTab === "overview" && (
            <>
              {selectedProject && (
                <DIN277Summary areas={areas} rooms={rooms} totalArea={selectedProject.total_area} />
              )}
              {selectedProject && (
                <AreaEfficiency
                  areas={areas}
                  totalArea={selectedProject.total_area}
                  buildingType={selectedProject.building_type}
                />
              )}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <AreaByFloorChart areas={areas} />
                <MaterialDistributionChart materials={materials} />
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {qualityReport && <QualityReport report={qualityReport} />}
                {costEstimate && <CostBreakdown estimate={costEstimate} />}
              </div>
            </>
          )}

          {activeTab === "rooms" && (
            <div className="space-y-6">
              <RoomCompletenessMatrix rooms={rooms} />
              <RoomTable rooms={rooms} />
            </div>
          )}

          {activeTab === "floors" && (
            <FloorOverview rooms={rooms} areas={areas} />
          )}

          {activeTab === "quantities" && (
            <QuantityTable quantities={quantities} totalCost={totalCost} />
          )}

          {activeTab === "costs" && costEstimate && (
            <CostBreakdown estimate={costEstimate} />
          )}

          {activeTab === "quality" && qualityReport && (
            <QualityReport report={qualityReport} />
          )}

          {activeTab === "lph" && lphProgress && (
            <LPHProgressCard data={lphProgress} />
          )}

          {activeTab === "changes" && selectedId && (
            <MonitoringDashboard
              projectId={selectedId}
              snapshots={snapshots}
              onSnapshotsChange={setSnapshots}
            />
          )}

          {activeTab === "reports" && selectedProject && (
            <ReportDownload projectId={selectedProject.id} projectName={selectedProject.name} />
          )}
        </>
      )}
    </div>
  );
}
