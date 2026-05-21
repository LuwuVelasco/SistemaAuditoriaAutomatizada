import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_PROGRESO_URL } from '../services/api';

/**
 * Hook para conexión WebSocket con reconexión automática.
 */
export function useWebSocket() {
  const [mensajes, setMensajes] = useState([]);
  const [ultimoMensaje, setUltimoMensaje] = useState(null);
  const [conectado, setConectado] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const conectar = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket('ws://127.0.0.1:8000/ws/progreso');

      ws.onopen = () => {
        setConectado(true);
        console.log('WebSocket conectado');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.tipo === 'pong') return;
          setMensajes(prev => [...prev, data]);
          setUltimoMensaje(data);
        } catch (e) {
          console.error('Error parseando WS:', e);
        }
      };

      ws.onclose = () => {
        setConectado(false);
        // Reconectar después de 3 segundos
        reconnectTimer.current = setTimeout(() => {
          conectar();
        }, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('Error creando WebSocket:', e);
    }
  }, []);

  const desconectar = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConectado(false);
  }, []);

  const limpiarMensajes = useCallback(() => {
    setMensajes([]);
    setUltimoMensaje(null);
  }, []);

  // Ping keepalive cada 30s
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping');
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => desconectar();
  }, [desconectar]);

  return {
    conectar,
    desconectar,
    conectado,
    mensajes,
    ultimoMensaje,
    limpiarMensajes,
  };
}
