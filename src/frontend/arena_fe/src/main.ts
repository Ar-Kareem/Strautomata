import { isDevMode } from '@angular/core';
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

const GA_MEASUREMENT_ID = 'G-TJHVZY279Q';

// Only load Google Analytics in production builds served from a real host.
if (!isDevMode() && !['localhost', '127.0.0.1'].includes(location.hostname)) {
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script);

  const w = window as any;
  w.dataLayer = w.dataLayer || [];
  w.gtag = function () { w.dataLayer.push(arguments); };
  w.gtag('js', new Date());
  w.gtag('config', GA_MEASUREMENT_ID);
}

bootstrapApplication(App, appConfig)
  .catch((err) => console.error(err));
