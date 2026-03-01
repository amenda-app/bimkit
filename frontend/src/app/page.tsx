export default function DashboardPage() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-dcab-navy text-white px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">
            DCAB BIM Report Studio
          </h1>
          <span className="text-sm text-dcab-light opacity-75">v0.1.0</span>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Connection Status */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-dcab-accent">
            <h2 className="text-sm font-semibold text-dcab-gray uppercase tracking-wide">
              Verbindung
            </h2>
            <p className="mt-2 text-2xl font-bold text-dcab-navy">
              Mock-Modus
            </p>
            <p className="text-sm text-dcab-gray mt-1">
              ArchiCAD nicht verbunden
            </p>
          </div>

          {/* Projects */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-dcab-blue">
            <h2 className="text-sm font-semibold text-dcab-gray uppercase tracking-wide">
              Projekte
            </h2>
            <p className="mt-2 text-2xl font-bold text-dcab-navy">3</p>
            <p className="text-sm text-dcab-gray mt-1">
              Verfügbare Projekte
            </p>
          </div>

          {/* Reports */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-dcab-navy">
            <h2 className="text-sm font-semibold text-dcab-gray uppercase tracking-wide">
              Berichte
            </h2>
            <p className="mt-2 text-2xl font-bold text-dcab-navy">
              Raumbuch, Flächen, Material
            </p>
            <p className="text-sm text-dcab-gray mt-1">3 Report-Typen</p>
          </div>
        </div>

        {/* Placeholder Content */}
        <div className="mt-8 bg-white rounded-lg shadow p-8 text-center">
          <p className="text-dcab-gray text-lg">
            Dashboard wird in der nächsten Phase implementiert.
          </p>
          <p className="text-sm text-dcab-gray mt-2">
            BIM Service läuft auf Port 8000 mit Mock-Daten.
          </p>
        </div>
      </main>
    </div>
  );
}
