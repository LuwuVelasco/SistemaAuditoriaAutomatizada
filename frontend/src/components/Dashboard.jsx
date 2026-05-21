import './Dashboard.css';
import HallazgoCard from './HallazgoCard';

/**
 * Dashboard de resultados de auditoría.
 */
export default function Dashboard({ resultado }) {
  if (!resultado) return null;

  const { hallazgos = [], resumen_riesgos = {}, contexto } = resultado;

  const statsCards = [
    { label: 'Total Hallazgos', value: hallazgos.length, icon: '🔍', color: 'var(--accent-primary)' },
    { label: 'Riesgo Extremo', value: resumen_riesgos['Extremo'] || 0, icon: '🔴', color: 'var(--risk-extremo)' },
    { label: 'Riesgo Alto', value: resumen_riesgos['Alto'] || 0, icon: '🟠', color: 'var(--risk-alto)' },
    { label: 'Riesgo Medio', value: resumen_riesgos['Medio'] || 0, icon: '🟡', color: 'var(--risk-medio)' },
  ];

  return (
    <div className="dashboard">
      {/* Entidad info */}
      {contexto && (
        <div className="entity-banner glass-card animate-fade-in">
          <div className="entity-icon">🏢</div>
          <div className="entity-info">
            <h2>{contexto.nombre_entidad}</h2>
            <div className="entity-details">
              <span>📅 {contexto.periodo_evaluado}</span>
              {contexto.grupo_auditor && <span>👥 {contexto.grupo_auditor}</span>}
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="stats-grid">
        {statsCards.map((stat, i) => (
          <div
            key={i}
            className="stat-card glass-card animate-slide-up"
            style={{ animationDelay: `${i * 0.1}s`, '--stat-color': stat.color }}
          >
            <span className="stat-icon">{stat.icon}</span>
            <span className="stat-value">{stat.value}</span>
            <span className="stat-label">{stat.label}</span>
          </div>
        ))}
      </div>

      {/* Risk distribution bar */}
      {hallazgos.length > 0 && (
        <div className="risk-distribution glass-card animate-fade-in">
          <h3>Distribución de Riesgos</h3>
          <div className="risk-bars">
            {['Extremo', 'Alto', 'Medio', 'Bajo', 'Muy Bajo'].map(nivel => {
              const count = resumen_riesgos[nivel] || 0;
              const pct = hallazgos.length > 0 ? (count / hallazgos.length) * 100 : 0;
              return (
                <div key={nivel} className="risk-dist-row">
                  <span className="risk-dist-label">{nivel}</span>
                  <div className="risk-dist-bar-bg">
                    <div
                      className="risk-dist-bar-fill"
                      style={{
                        width: `${pct}%`,
                        background: `var(--risk-${nivel.toLowerCase().replace(' ', '-')})`,
                      }}
                    ></div>
                  </div>
                  <span className="risk-dist-count">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Hallazgos list */}
      <div className="hallazgos-section">
        <h3 className="section-title">
          <span>📋 Hallazgos Detallados</span>
          <span className="count-badge">{hallazgos.length}</span>
        </h3>
        <div className="hallazgos-list">
          {hallazgos.map((h, i) => (
            <HallazgoCard key={h.codigo} hallazgo={h} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
