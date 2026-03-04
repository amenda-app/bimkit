import { Dashboard } from "@/components/Dashboard";

export default function DashboardPage() {
  return (
    <div className="min-h-screen">
      <header className="bg-dcab-navy text-white px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">
            DCAB BIM Report Studio
          </h1>
          <span className="text-sm text-dcab-light opacity-75">v0.1.0</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        <Dashboard />
      </main>
    </div>
  );
}
