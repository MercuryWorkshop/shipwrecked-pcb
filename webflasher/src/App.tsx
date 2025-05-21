import React, { useEffect, useState } from 'react';
import './App.css';
import ConnectionSettings from './components/ConnectionSettings';
import { MicroPythonProvider } from './MicroPythonContext';
import { DeviceStateProvider } from './DeviceStateContext';
import Layout from './components/Layout';
import FirmwarePanel from './components/FirmwarePanel';
import ConfigurationPanel from './components/ConfigurationPanel';
import AppManager from './components/apps/AppManager';
import HelpModal from './components/HelpModal';
import { App as AppType } from './components/apps/AppListItem';

function App() {
  const [apps, setApps] = useState<AppType[]>([]);
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  useEffect(() => {
    document.title = 'Shipwrecked PCB flasher';
  }, []);
  
  return (
    <MicroPythonProvider>
      <DeviceStateProvider>
        <div className="App">
          <button 
            className="help-button" 
            onClick={() => setIsHelpOpen(true)}
            title="Learn how to use the Badge Flasher"
          >
            <span className="help-icon">?</span>
            <span>Help</span>
          </button>

          <Layout
            leftPane={
              <>
                <ConnectionSettings />
                <FirmwarePanel />
              </>
            }
            middlePane={<ConfigurationPanel />}
            rightPane={<AppManager apps={apps} onAppListChange={setApps} />}
          />

          <HelpModal 
            isOpen={isHelpOpen} 
            onClose={() => setIsHelpOpen(false)} 
          />
        </div>
      </DeviceStateProvider>
    </MicroPythonProvider>
  );
}

export default App;
