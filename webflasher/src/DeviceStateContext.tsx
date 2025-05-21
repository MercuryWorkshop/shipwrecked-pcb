import React, { createContext, useContext, useState, useCallback } from 'react';

type DeviceStateContextType = {
  needsRefresh: boolean;
  isScanning: boolean;
  firmwareStatus: 'checking' | 'ready' | 'updating' | 'idle';
  triggerRefresh: () => void;
  setIsScanning: (scanning: boolean) => void;
  setFirmwareStatus: (status: 'checking' | 'ready' | 'updating' | 'idle') => void;
};

const DeviceStateContext = createContext<DeviceStateContextType>({
  needsRefresh: false,
  isScanning: false,
  firmwareStatus: 'idle',
  triggerRefresh: () => {},
  setIsScanning: () => {},
  setFirmwareStatus: () => {},
});

export const useDeviceState = () => useContext(DeviceStateContext);

export function DeviceStateProvider({ children }: { children: React.ReactNode }) {
  const [needsRefresh, setNeedsRefresh] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [firmwareStatus, setFirmwareStatus] = useState<'checking' | 'ready' | 'updating' | 'idle'>('idle');

  const triggerRefresh = useCallback(() => {
    setNeedsRefresh(true);
    // Reset after a short delay to allow components to detect the change
    setTimeout(() => setNeedsRefresh(false), 100);
  }, []);

  return (
    <DeviceStateContext.Provider 
      value={{ 
        needsRefresh,
        isScanning,
        firmwareStatus,
        triggerRefresh,
        setIsScanning,
        setFirmwareStatus
      }}
    >
      {children}
    </DeviceStateContext.Provider>
  );
}
