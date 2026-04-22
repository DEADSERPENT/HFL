import React from 'react';
import { useFLStore } from './store/useFLStore';
import { useSimulation } from './hooks/useSimulation';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard }   from './pages/Dashboard';
import { Clients }     from './pages/Clients';
import { Training }    from './pages/Training';
import { Experiments } from './pages/Experiments';
import { Logs }        from './pages/Logs';
import { Settings }    from './pages/Settings';

function PageRouter() {
  const { currentPage } = useFLStore();
  switch (currentPage) {
    case 'dashboard':   return <Dashboard />;
    case 'clients':     return <Clients />;
    case 'training':    return <Training />;
    case 'experiments': return <Experiments />;
    case 'logs':        return <Logs />;
    case 'settings':    return <Settings />;
    default:            return <Dashboard />;
  }
}

export default function App() {
  useSimulation();

  return (
    <AppLayout>
      <PageRouter />
    </AppLayout>
  );
}
