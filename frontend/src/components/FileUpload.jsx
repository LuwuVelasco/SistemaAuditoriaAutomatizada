import { useCallback, useState, useRef } from 'react';
import './FileUpload.css';

/**
 * Componente de drag-and-drop para subir documentos.
 */
export default function FileUpload({ onUpload, cargando }) {
  const [dragActive, setDragActive] = useState(false);
  const [archivosSeleccionados, setArchivosSeleccionados] = useState([]);
  const inputRef = useRef(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = [...e.dataTransfer.files].filter(f =>
      f.name.endsWith('.pdf') || f.name.endsWith('.docx') || f.name.endsWith('.doc')
    );

    if (files.length > 0) {
      setArchivosSeleccionados(files);
      onUpload(files);
    }
  }, [onUpload]);

  const handleChange = useCallback((e) => {
    const files = [...e.target.files];
    if (files.length > 0) {
      setArchivosSeleccionados(files);
      onUpload(files);
    }
  }, [onUpload]);

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <div className="file-upload-container">
      <div
        className={`drop-zone ${dragActive ? 'drag-active' : ''} ${cargando ? 'loading' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.doc"
          onChange={handleChange}
          className="file-input-hidden"
        />

        <div className="drop-zone-content">
          {cargando ? (
            <>
              <div className="upload-spinner"></div>
              <p className="drop-text">Subiendo archivos...</p>
            </>
          ) : (
            <>
              <div className="upload-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              </div>
              <p className="drop-text">
                Arrastra tus documentos aquí
              </p>
              <p className="drop-subtext">
                o haz clic para seleccionar
              </p>
              <div className="file-types">
                <span className="file-badge">PDF</span>
                <span className="file-badge">DOCX</span>
              </div>
            </>
          )}
        </div>
      </div>

      {archivosSeleccionados.length > 0 && !cargando && (
        <div className="selected-files animate-fade-in">
          <p className="selected-label">
            ✅ {archivosSeleccionados.length} archivo(s) subido(s)
          </p>
          {archivosSeleccionados.map((file, i) => (
            <div key={i} className="selected-file">
              <span className="file-icon">
                {file.name.endsWith('.pdf') ? '📄' : '📝'}
              </span>
              <span className="file-name">{file.name}</span>
              <span className="file-size">{formatSize(file.size)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
