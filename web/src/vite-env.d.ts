/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Absolute API base for native builds (Capacitor). Web leaves it unset and
   * derives the base from BASE_URL. */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
