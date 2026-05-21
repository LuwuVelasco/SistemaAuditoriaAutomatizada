import { useEffect } from 'react';
import { getUrlDescarga } from '../services/api';
import './ExportPanel.css';

const FILE_ICONS = {
  docx: { icon: '📝', label: 'Word', color: '#2b579a' },
  xlsx: { icon: '📊', label: 'Excel', color: '#217346' },
  json: { icon: '📋', label: 'JSON', color: '#6c63ff' },
};

/**
 * Panel de descarga de documentos generados.
 */
export default function ExportPanel({ archivos, onRefresh }) {
  useEffect(() => {
    onRefresh?.();
  }, []);

  if (!archivos || archivos.length === 0) {
    return (
      <div className="export-panel glass-card animate-fade-in">
        <div className="export-empty">
          <span className="export-empty-icon">📦</span>
          <p>No hay documentos generados aún</p>
          <p className="export-empty-sub">Ejecuta una auditoría para generar los documentos</p>
        </div>
      </div>
    );
  }

  return (
    <div className="export-panel animate-fade-in">
      <h3 className="export-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Documentos Generados
        <span className="count-badge">{archivos.length}</span>
      </h3>

      <div className="export-grid">
        {archivos.map((archivo, i) => {
          const ext = archivo.tipo || archivo.nombre?.split('.').pop();
          const fileInfo = FILE_ICONS[ext] || FILE_ICONS.json;
          const sizeKB = archivo.tamano ? (archivo.tamano / 1024).toFixed(1) : '?';

          return (
            <a
              key={i}
              href={getUrlDescarga(archivo.nombre)}
              download
              className="export-card glass-card"
              style={{ animationDelay: `${i * 0.1}s`, '--file-color': fileInfo.color }}
            >
              <div className="export-card-icon">{fileInfo.icon}</div>
              <div className="export-card-info">
                <span className="export-card-name">{archivo.nombre}</span>
                <span className="export-card-meta">
                  {fileInfo.label} · {sizeKB} KB
                </span>
              </div>
              <div className="export-card-action">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
