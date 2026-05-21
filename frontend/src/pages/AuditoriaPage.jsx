import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ProgressTracker from '../components/ProgressTracker';
import { useWebSocket } from '../hooks/useWebSocket';
import { healthCheck } from '../services/api';
import './AuditoriaPage.css';

export default function AuditoriaPage({ auditState }) {
  const {
    documentos,
    auditando,
    iniciarAuditoria,
    error,
    limpiarError,
    setResultado,
  } = auditState;

  const navigate = useNavigate();
  const ws = useWebSocket();

  const [form, setForm] = useState({
    nombre_grupo: '',
    integrantes: '',
    alcance: '',
  });

  const [health, setHealth] = useState({ status: 'checking', gemini: false });

  // Comprobar estado de Gemini al cargar
  useEffect(() => {
    healthCheck().then(res => {
      setHealth({ status: res.status, gemini: res.gemini_disponible });
    });
  }, []);

  // Conectar WS solo cuando se está auditando
  useEffect(() => {
    if (auditando) {
      ws.conectar();
    } else {
      ws.desconectar();
    }
  }, [auditando, ws]);

  // Si el WS envía estado completado, cargar resultados
  useEffect(() => {
    if (ws.ultimoMensaje?.tipo === 'completado') {
      setResultado(ws.ultimoMensaje.resultado);
      setTimeout(() => navigate('/resultados'), 1500);
    }
  }, [ws.ultimoMensaje, navigate, setResultado]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (documentos.length === 0) {
      alert('Sube al menos un documento antes de iniciar la auditoría');
      return;
    }

    const config = {
      nombre_grupo: form.nombre_grupo,
      integrantes: form.integrantes.split(',').map(s => s.trim()).filter(Boolean),
      alcance: form.alcance,
    };

    ws.limpiarMensajes();
    iniciarAuditoria(config);
  };

  return (
    <div className="page-container animate-fade-in">
      <header className="page-header">
        <div>
          <h1>Ejecutar Auditoría</h1>
          <p>Configura los parámetros e inicia el proceso automatizado RAG (Google Gemini).</p>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={limpiarError}>✕</button>
        </div>
      )}

      {!health.gemini && health.status === 'ok' && (
        <div className="warning-banner">
          <span>⚠️ Gemini API no está en ejecución. El análisis fallará. Por favor, verifica la API Key.</span>
        </div>
      )}

      <div className="auditoria-content">
        {!auditando ? (
          <form className="config-form glass-card animate-slide-up" onSubmit={handleSubmit}>
            <h3>Configuración de la Auditoría</h3>

            <div className="form-group">
              <label>Nombre del Grupo Auditor</label>
              <input
                type="text"
                placeholder="Ej. Grupo de Auditoría TI"
                value={form.nombre_grupo}
                onChange={e => setForm({ ...form, nombre_grupo: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Integrantes (separados por coma)</label>
              <input
                type="text"
                placeholder="Juan Pérez, María Gómez"
                value={form.integrantes}
                onChange={e => setForm({ ...form, integrantes: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Alcance (Opcional)</label>
              <textarea
                placeholder="Define el alcance específico de esta evaluación..."
                value={form.alcance}
                onChange={e => setForm({ ...form, alcance: e.target.value })}
                rows={3}
              />
            </div>

            <div className="form-footer">
              <div className="docs-status">
                <span className="status-dot" style={{ background: documentos.length > 0 ? 'var(--accent-success)' : 'var(--text-muted)' }}></span>
                {documentos.length} documento(s) listos para análisis
              </div>

              <button
                type="submit"
                className="btn-primary"
                disabled={documentos.length === 0 || !health.gemini}
              >
                <span>🚀</span>
                Iniciar Auditoría Automatizada
              </button>
            </div>
          </form>
        ) : (
          <div className="progress-section glass-card animate-slide-up">
            <h3>Estado del Procesamiento IA</h3>
            <p className="progress-desc">
              El agente está enviando los documentos a Gemini, extrayendo contexto y evaluando controles.
            </p>
            <ProgressTracker
              progreso={ws.ultimoMensaje}
              mensajes={ws.mensajes}
            />
          </div>
        )}
      </div>
    </div>
  );
}
