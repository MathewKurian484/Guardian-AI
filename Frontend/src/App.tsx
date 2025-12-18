import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AppStateProvider } from '@/contexts/AppStateContext';
import Navbar from '@/components/Navbar';
import Dashboard from '@/pages/Dashboard';
import CodeAudit from '@/pages/CodeAudit';
import QAChat from '@/pages/QAChat';

function App() {
  return (
    <ThemeProvider>
      <AppStateProvider>
        <Router>
          <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-800 transition-colors duration-300">
            <Navbar />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/audit" element={<CodeAudit />} />
              <Route path="/qa" element={<QAChat />} />
            </Routes>
          </div>
        </Router>
      </AppStateProvider>
    </ThemeProvider>
  );
}

export default App;
