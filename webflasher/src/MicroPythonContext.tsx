import React, { createContext, useContext, useState, useCallback } from 'react';
// @ts-ignore
import { MicroPython } from './micropython-webserial.js';
import { AsyncQueue } from './AsyncQueue';

// Wrap MicroPython methods to use queue
class QueuedMicroPython {
  private mp: MicroPython;
  private queue: AsyncQueue;

  constructor(mp: MicroPython) {
    this.mp = mp;
    this.queue = new AsyncQueue();
  }

  async connect() {
    return this.queue.enqueue(() => this.mp.connect());
  }

  async disconnect() {
    return this.queue.enqueue(() => this.mp.disconnect());
  }

  async listFiles() {
    return this.queue.enqueue(() => this.mp.listFiles());
  }

  async downloadFileToString(path: string) {
    return this.queue.enqueue(() => this.mp.downloadFileToString(path));
  }

  async uploadFile(path: string, content: Uint8Array) {
    return this.queue.enqueue(() => this.mp.uploadFile(path, content));
  }

  async createFolder(path: string) {
    return this.queue.enqueue(() => this.mp.createFolder(path));
  }

  async removeFolder(path: string) {
    return this.queue.enqueue(() => this.mp.removeFolder(path));
  }

  async uploadFileFromString(path: string, content: string) {
    return this.queue.enqueue(() => this.mp.uploadFileFromString(path, content));
  }
}

type MicroPythonContextType = {
  mp: QueuedMicroPython | null;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  error: Error | null;
};

export const MicroPythonContext = createContext<MicroPythonContextType>({
  mp: null,
  isConnected: false,
  connect: async () => {},
  disconnect: async () => {},
  error: null,
});

type Props = { children: React.ReactNode };

export function MicroPythonProvider({ children }: Props) {
  const [mp, setMp] = useState<QueuedMicroPython | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const connect = useCallback(async () => {
    try {
      const baseMp = new MicroPython();
      const mpInstance = new QueuedMicroPython(baseMp);
      await mpInstance.connect();
      setMp(mpInstance);
      setIsConnected(true);
      setError(null);
    } catch (e: any) {
      setError(e instanceof Error ? e : new Error(String(e)));
      setIsConnected(false);
      setMp(null);
    }
  }, []);

  const disconnect = useCallback(async () => {
    if (mp) {
      await mp.disconnect();
      setIsConnected(false);
      setMp(null);
    }
  }, [mp]);

  return (
    <MicroPythonContext.Provider value={{ mp, isConnected, connect, disconnect, error }}>
      {children}
    </MicroPythonContext.Provider>
  );
}

export function useMicroPython() {
  return useContext(MicroPythonContext);
}
