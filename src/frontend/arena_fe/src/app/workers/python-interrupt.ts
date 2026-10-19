/**
 * Stops Python code running in a Pyodide worker without killing the worker.
 *
 * Pyodide polls a shared Int32Array while Python runs and raises KeyboardInterrupt when slot 0
 * holds 2 (SIGINT). Killing the worker instead throws away the whole runtime (Pyodide, OpenSpiel,
 * game engines), which takes seconds to load again. Needs SharedArrayBuffer, i.e. a cross-origin
 * isolated page (see public/coi-serviceworker.js); without it `supported` is false and callers
 * fall back to terminating the worker.
 *
 * Shared slots: [0] Pyodide's signal slot, [1] 1 while the host is stopping the worker. The worker
 * clears [1] when it answers the 'ping' that follows the interrupt, so stale requests queued in
 * between are interrupted too and requests sent after the ping run normally.
 */
export const INTERRUPT_SIGNAL_SLOT = 0;
export const INTERRUPT_PENDING_SLOT = 1;
const SIGINT = 2;
/** a policy with a bare `except:` swallows one KeyboardInterrupt, so keep raising until it gives up */
const RESEND_MS = 50;
/** how long Python gets to unwind after the interrupt before the worker is killed instead */
export const INTERRUPT_GRACE_MS = 1500;

export class PythonInterrupt {
  static readonly supported = typeof SharedArrayBuffer !== 'undefined' && globalThis.crossOriginIsolated === true;

  readonly buffer = new Int32Array(new SharedArrayBuffer(8));

  /** hand the buffer to a freshly created worker (before any other request) */
  attach(worker: Worker): void {
    worker.postMessage({ type: 'setInterruptBuffer', buffer: this.buffer });
  }

  /**
   * Interrupt whatever Python the worker is running. `ping` must post a 'ping' request to the worker
   * and resolve once it is answered. Resolves true if the worker came back within the grace period.
   */
  async stop(ping: () => Promise<unknown>, graceMs = INTERRUPT_GRACE_MS): Promise<boolean> {
    const raise = () => {
      if (Atomics.load(this.buffer, INTERRUPT_PENDING_SLOT) === 1) {
        Atomics.store(this.buffer, INTERRUPT_SIGNAL_SLOT, SIGINT);
      }
    };
    Atomics.store(this.buffer, INTERRUPT_PENDING_SLOT, 1);
    raise();
    const resend = setInterval(raise, RESEND_MS);
    let timer: ReturnType<typeof setTimeout> | null = null;
    try {
      return await Promise.race([
        ping().then(() => true, () => true),
        new Promise<boolean>((resolve) => {
          timer = setTimeout(() => resolve(false), graceMs);
        })
      ]);
    } finally {
      clearInterval(resend);
      if (timer !== null) {
        clearTimeout(timer);
      }
      Atomics.store(this.buffer, INTERRUPT_PENDING_SLOT, 0);
    }
  }
}
