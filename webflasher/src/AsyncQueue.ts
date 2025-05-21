export class AsyncQueue {
  private queue: (() => Promise<any>)[] = [];
  private processing = false;

  async enqueue<T>(operation: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await operation();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.processing || this.queue.length === 0) return;

    this.processing = true;
    try {
      const operation = this.queue.shift();
      if (operation) {
        await operation();
      }
    } finally {
      this.processing = false;
      if (this.queue.length > 0) {
        // Process next item in queue
        this.processQueue();
      }
    }
  }
}
