import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Dashboard from '../components/Dashboard';
import ExportPanel from '../components/ExportPanel';
import './ResultadosPage.css';

export default function ResultadosPage({ auditState }) {
  const {
    resultado,
    archivosGenerados,
    cargarResultados,
    cargarArchivos,
  } = auditState;

  const navigate = useNavigate();

  useEffect(() => {
    cargarResultados();
    cargarArchivos();
  }, [cargarResultados, cargarArchivos]);

  if (!resultado) {
    return (
      <div className="page-container animate-fade-in">
        <header className="page-header">
          <div>
            <h1>Resultados de Auditoría</h1>
            <p>Aún no hay resultados disponibles.</p>
          </div>
        </header>

        <div className="no-results glass-card">
          <span className="no-results-icon">📊</span>
          <h2>No hay datos para mostrar</h2>
          <p>Debes ejecutar una auditoría primero para ver los resultados aquí.</p>
          <button className="btn-primary mt-lg" onClick={() => navigate('/auditoria')}>
            Ir a Auditoría
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in">
      <header className="page-header">
        <div>
          <h1>Resultados de Auditoría</h1>
          <p>Revisa los hallazgos identificados y descarga los informes generados.</p>
        </div>
      </header>

      <div className="resultados-layout">
        {/* Columna Izquierda: Dashboard */}
        <div className="dashboard-col">
          <Dashboard resultado={resultado} />
        </div>

        {/* Columna Derecha: Exportación */}
        <div className="export-col">
          <ExportPanel
            archivos={archivosGenerados}
            onRefresh={cargarArchivos}
          />
        </div>
      </div>
    </div>
  );
}
