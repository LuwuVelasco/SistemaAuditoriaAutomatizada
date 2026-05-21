import { useState, useCallback } from 'react';
import * as api from '../services/api';

/**
 * Hook para gestionar el estado de la auditoría.
 */
export function useAudit() {
  const [documentos, setDocumentos] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [auditando, setAuditando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [archivosGenerados, setArchivosGenerados] = useState([]);
  const [error, setError] = useState(null);

  const cargarDocumentos = useCallback(async () => {
    try {
      const data = await api.listarDocumentos();
      setDocumentos(data.documentos || []);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  const subirArchivos = useCallback(async (files) => {
    setCargando(true);
    setError(null);
    try {
      await api.uploadDocumentos(files);
      await cargarDocumentos();
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }, [cargarDocumentos]);

  const eliminarDocumento = useCallback(async (nombre) => {
    try {
      await api.eliminarDocumento(nombre);
      await cargarDocumentos();
    } catch (e) {
      setError(e.message);
    }
  }, [cargarDocumentos]);

  const eliminarTodos = useCallback(async () => {
    try {
      await api.eliminarTodosDocumentos();
      setDocumentos([]);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  const iniciarAuditoria = useCallback(async (config = {}) => {
    setAuditando(true);
    setError(null);
    setResultado(null);
    try {
      await api.iniciarAuditoria(config);
    } catch (e) {
      setError(e.message);
      setAuditando(false);
    }
  }, []);

  const cargarResultados = useCallback(async () => {
    try {
      const data = await api.obtenerResultados();
      setResultado(data);
      setAuditando(false);
    } catch (e) {
      // No hay resultados aún
    }
  }, []);

  const cargarArchivos = useCallback(async () => {
    try {
      const data = await api.listarArchivosGenerados();
      setArchivosGenerados(data.archivos || []);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  const limpiarError = useCallback(() => setError(null), []);

  return {
    documentos,
    cargando,
    auditando,
    setAuditando,
    resultado,
    setResultado,
    archivosGenerados,
    error,
    cargarDocumentos,
    subirArchivos,
    eliminarDocumento,
    eliminarTodos,
    iniciarAuditoria,
    cargarResultados,
    cargarArchivos,
    limpiarError,
  };
}
