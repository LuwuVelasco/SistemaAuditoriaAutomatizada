import { useState } from 'react';
import './HallazgoCard.css';

const RISK_COLORS = {
  'Muy Bajo': 'var(--risk-muy-bajo)',
  'Bajo': 'var(--risk-bajo)',
  'Medio': 'var(--risk-medio)',
  'Alto': 'var(--risk-alto)',
  'Extremo': 'var(--risk-extremo)',
};

/**
 * Card expandible para un hallazgo individual.
 */
export default function HallazgoCard({ hallazgo, index }) {
  const [expandido, setExpandido] = useState(false);
  const riesgoColor = RISK_COLORS[hallazgo.nivel_riesgo] || 'var(--text-muted)';
  const riesgoValor = hallazgo.probabilidad * hallazgo.impacto;

  return (
    <div
      className={`hallazgo-card glass-card animate-slide-up`}
      style={{ animationDelay: `${index * 0.08}s` }}
    >
      {/* Header */}
      <div className="hallazgo-header" onClick={() => setExpandido(!expandido)}>
        <div className="hallazgo-left">
          <span className="hallazgo-codigo">{hallazgo.codigo}</span>
          <div className="hallazgo-meta">
            <h3 className="hallazgo-titulo">
              {hallazgo.descripcion.length > 120
                ? hallazgo.descripcion.substring(0, 120) + '...'
                : hallazgo.descripcion}
            </h3>
            <div className="hallazgo-tags">
              {hallazgo.procesos?.map(p => (
                <span key={p} className="tag">{p}</span>
              ))}
            </div>
          </div>
        </div>

        <div className="hallazgo-right">
          <div className="risk-badge" style={{ '--risk-color': riesgoColor }}>
            <span className="risk-value">{riesgoValor}</span>
            <span className="risk-label">{hallazgo.nivel_riesgo}</span>
          </div>
          <button className="expand-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              style={{ transform: expandido ? 'rotate(180deg)' : 'rotate(0)' }}>
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Body expandido */}
      {expandido && (
        <div className="hallazgo-body animate-fade-in">
          <div className="detail-grid">
            <div className="detail-section">
              <h4>📋 Descripción</h4>
              <p>{hallazgo.descripcion}</p>
            </div>

            <div className="detail-section">
              <h4>🔍 Dominio y Procesos</h4>
              <p><strong>Dominio:</strong> {hallazgo.dominio}</p>
              <p><strong>Procesos:</strong> {hallazgo.procesos?.join(', ')}</p>
            </div>

            <div className="detail-section">
              <h4>⚠️ Causa</h4>
              <p>{hallazgo.causa}</p>
            </div>

            <div className="detail-section">
              <h4>💥 Efecto</h4>
              <p>{hallazgo.efecto}</p>
            </div>

            <div className="detail-section full-width">
              <h4>✅ Recomendación</h4>
              <p>{hallazgo.recomendacion}</p>
            </div>

            <div className="detail-section full-width">
              <h4>📊 Conclusión</h4>
              <p>{hallazgo.conclusion}</p>
            </div>

            {/* Nivel de Riesgo visual */}
            <div className="detail-section">
              <h4>📈 Nivel de Riesgo</h4>
              <div className="risk-matrix">
                <div className="risk-item">
                  <span className="risk-label-sm">Probabilidad</span>
                  <div className="risk-bar-container">
                    <div className="risk-bar" style={{ width: `${hallazgo.probabilidad * 20}%`, background: riesgoColor }}></div>
                  </div>
                  <span className="risk-num">{hallazgo.probabilidad}/5</span>
                </div>
                <div className="risk-item">
                  <span className="risk-label-sm">Impacto</span>
                  <div className="risk-bar-container">
                    <div className="risk-bar" style={{ width: `${hallazgo.impacto * 20}%`, background: riesgoColor }}></div>
                  </div>
                  <span className="risk-num">{hallazgo.impacto}/5</span>
                </div>
              </div>
            </div>

            {/* Citas bibliográficas */}
            {hallazgo.citas_bibliograficas?.length > 0 && (
              <div className="detail-section full-width">
                <h4>📚 Citas Bibliográficas</h4>
                <div className="citas-list">
                  {hallazgo.citas_bibliograficas.map((cita, i) => (
                    <div key={i} className="cita-item">
                      <span className="cita-num">{i + 1}</span>
                      <div>
                        <strong>{cita.documento}, {cita.seccion}</strong>
                        {cita.pagina && <span className="cita-page"> — {cita.pagina}</span>}
                        <p className="cita-desc">{cita.descripcion}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
