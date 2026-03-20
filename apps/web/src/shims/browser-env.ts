type BrowserProcess = {
  env: Record<string, string>;
  browser: boolean;
};

const browserGlobal = globalThis as any;

if (!browserGlobal.global) {
  browserGlobal.global = browserGlobal;
}

if (!browserGlobal.process) {
  browserGlobal.process = {
    env: {},
    browser: true,
  } as BrowserProcess;
} else {
  const browserProcess = browserGlobal.process as unknown as BrowserProcess;
  browserProcess.env ??= {};
  browserProcess.browser ??= true;
}

export {};
