import { useEffect } from 'react';
import FileUpload from '../components/FileUpload';
import './DocumentosPage.css';

export default function DocumentosPage({ auditState }) {
  const {
    documentos,
    cargando,
    error,
    cargarDocumentos,
    subirArchivos,
    eliminarDocumento,
    eliminarTodos,
    limpiarError,
  } = auditState;

  useEffect(() => {
    cargarDocumentos();
  }, [cargarDocumentos]);

  return (
    <div className="page-container animate-fade-in">
      <header className="page-header">
        <div>
          <h1>Gestión de Documentos</h1>
          <p>Sube los manuales, políticas y procedimientos de la entidad a auditar.</p>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={limpiarError}>✕</button>
        </div>
      )}

      <div className="documentos-content">
        <section className="upload-section">
          <h2>Subir Nuevos Archivos</h2>
          <FileUpload onUpload={subirArchivos} cargando={cargando} />
        </section>

        <section className="list-section glass-card">
          <div className="list-header">
            <h2>Documentos Indexados ({documentos.length})</h2>
            {documentos.length > 0 && (
              <button className="btn-danger" onClick={eliminarTodos}>
                🗑️ Eliminar Todos
              </button>
            )}
          </div>

          {documentos.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon">📂</span>
              <p>No hay documentos en el sistema</p>
            </div>
          ) : (
            <div className="docs-grid">
              {documentos.map((doc, i) => (
                <div
                  key={doc.nombre}
                  className="doc-card animate-slide-up"
                  style={{ animationDelay: `${i * 0.05}s` }}
                >
                  <div className="doc-icon">
                    {doc.tipo === 'pdf' ? '📄' : '📝'}
                  </div>
                  <div className="doc-info">
                    <h4 title={doc.nombre}>{doc.nombre}</h4>
                    <span>{(doc.tamano / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                  <button
                    className="btn-icon-danger"
                    onClick={() => eliminarDocumento(doc.nombre)}
                    title="Eliminar documento"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
