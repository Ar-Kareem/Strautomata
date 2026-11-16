/*
 * Makes the page cross-origin isolated on hosts that cannot set response headers (GitHub Pages).
 * Isolation enables SharedArrayBuffer, which lets the app interrupt a stuck Python policy inside
 * its Pyodide worker instead of killing and reloading the whole runtime.
 *
 * Loaded twice: as a classic <script> in index.html, where it registers itself as a service worker
 * (and reloads once, the first time, so the page comes back under it), and as that service worker,
 * where it adds COOP/COEP to same-origin pages and worker scripts. Cross-origin requests are left alone;
 * the CDNs the site uses (jsDelivr, Google Fonts) already send the CORS/CORP headers COEP needs.
 */
if (typeof window === 'undefined') {
  self.addEventListener('install', () => self.skipWaiting());
  self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
  self.addEventListener('fetch', (event) => {
    const request = event.request;
    // only documents and workers carry the isolation headers; everything else passes through
    const isDocument = request.mode === 'navigate';
    if (!isDocument && request.destination !== 'worker') {
      return;
    }
    if (request.method !== 'GET' || new URL(request.url).origin !== self.location.origin) {
      return;
    }
    event.respondWith(
      fetch(request).then((response) => {
        const type = response.headers.get('Content-Type') || '';
        if (response.status === 0 || (isDocument && !type.includes('text/html'))) {
          return response; // e.g. the paper PDF: leave the browser's viewer alone
        }
        const headers = new Headers(response.headers);
        headers.set('Cross-Origin-Opener-Policy', 'same-origin');
        headers.set('Cross-Origin-Embedder-Policy', 'require-corp');
        return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
      })
    );
  });
} else if (!window.crossOriginIsolated && window.isSecureContext && 'serviceWorker' in navigator) {
  const script = document.currentScript.src;
  navigator.serviceWorker.register(script).then(
    (registration) => {
      // reload once when the worker first takes control; a browser that still is not isolated
      // under it (e.g. isolation disabled by policy) must not reload forever
      const reloadedKey = 'coiReloaded';
      const reload = () => {
        if (!sessionStorage.getItem(reloadedKey)) {
          sessionStorage.setItem(reloadedKey, '1');
          window.location.reload();
        }
      };
      if (navigator.serviceWorker.controller) {
        reload(); // controlled but not isolated: the worker was just updated
      } else {
        navigator.serviceWorker.addEventListener('controllerchange', reload);
      }
      registration.update();
    },
    (error) => console.warn('Cross-origin isolation service worker failed to register', error)
  );
} else if (window.crossOriginIsolated) {
  sessionStorage.removeItem('coiReloaded');
}
