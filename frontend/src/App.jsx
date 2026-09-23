import React from 'react';
import { RealtimeProvider } from './context/RealtimeContext';
import OperatorConsole from './components/OperatorConsole';

function App() {
  return (
    <RealtimeProvider>
      <OperatorConsole />
    </RealtimeProvider>
  );
}

export default App;
