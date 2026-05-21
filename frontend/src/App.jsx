import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import DocumentosPage from './pages/DocumentosPage';
import AuditoriaPage from './pages/AuditoriaPage';
import ResultadosPage from './pages/ResultadosPage';
import { useAudit } from './hooks/useAudit';

function App() {
  const auditState = useAudit();

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DocumentosPage auditState={auditState} />} />
        <Route path="/auditoria" element={<AuditoriaPage auditState={auditState} />} />
        <Route path="/resultados" element={<ResultadosPage auditState={auditState} />} />
      </Routes>
    </Layout>
  );
}

export default App;
