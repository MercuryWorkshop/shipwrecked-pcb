interface SerialOptions {
  baudRate: number;
}

interface SerialPort {
  readable?: ReadableStream<Uint8Array>;
  writable?: WritableStream<Uint8Array>;
  open(options: SerialOptions): Promise<void>;
  close(): Promise<void>;
}

interface Serial {
  requestPort(): Promise<SerialPort>;
}

declare global {
  interface Navigator {
    serial: Serial;
  }
}

export {};
