import './ProgressTracker.css';

/**
 * Componente de seguimiento de progreso de la auditoría.
 */
export default function ProgressTracker({ progreso, mensajes }) {
  const pasos = [
    { num: 1, label: 'Procesar Documentos', icon: '📄' },
    { num: 2, label: 'Extraer Contexto', icon: '🏢' },
    { num: 3, label: 'Vectorizar', icon: '🧮' },
    { num: 4, label: 'Auditoría COBIT', icon: '🤖' },
    { num: 5, label: 'Evaluación COSO', icon: '📋' },
    { num: 6, label: 'Generar Documentos', icon: '📊' },
  ];

  const pasoActual = progreso?.paso || 0;
  const porcentaje = progreso?.porcentaje || 0;
  const completado = progreso?.estado === 'completado';
  const conError = progreso?.estado === 'error' || progreso?.tipo === 'error';

  return (
    <div className="progress-tracker">
      {/* Barra de progreso global */}
      <div className="progress-bar-container">
        <div className="progress-bar-bg">
          <div
            className={`progress-bar-fill ${completado ? 'completed' : ''} ${conError ? 'error' : ''}`}
            style={{ width: `${porcentaje}%` }}
          >
            {porcentaje > 5 && (
              <div className="progress-shimmer"></div>
            )}
          </div>
        </div>
        <span className="progress-percentage">
          {completado ? '✅' : conError ? '❌' : `${Math.round(porcentaje)}%`}
        </span>
      </div>

      {/* Mensaje actual */}
      {progreso?.mensaje && (
        <div className={`progress-message ${completado ? 'success' : ''} ${conError ? 'error' : ''}`}>
          {progreso.mensaje}
        </div>
      )}

      {/* Pasos */}
      <div className="steps-container">
        {pasos.map((paso) => {
          const isActive = pasoActual === paso.num;
          const isDone = pasoActual > paso.num || completado;
          const isPending = pasoActual < paso.num && !completado;

          return (
            <div
              key={paso.num}
              className={`step ${isActive ? 'active' : ''} ${isDone ? 'done' : ''} ${isPending ? 'pending' : ''}`}
            >
              <div className="step-indicator">
                {isDone ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                ) : isActive ? (
                  <div className="step-spinner"></div>
                ) : (
                  <span>{paso.num}</span>
                )}
              </div>
              <div className="step-info">
                <span className="step-icon">{paso.icon}</span>
                <span className="step-label">{paso.label}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Log de mensajes */}
      {mensajes.length > 0 && (
        <div className="progress-log">
          <div className="log-header">
            <span>📋 Log de actividad</span>
            <span className="log-count">{mensajes.length}</span>
          </div>
          <div className="log-entries">
            {mensajes.slice(-8).map((msg, i) => (
              <div key={i} className={`log-entry ${msg.tipo === 'error' ? 'error' : ''} ${msg.tipo === 'completado' ? 'success' : ''}`}>
                <span className="log-time">
                  {new Date().toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
                <span className="log-text">{msg.mensaje}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
