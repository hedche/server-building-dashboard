/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_NAME?: string
  readonly VITE_BACKEND_URL?: string
  readonly VITE_DEV_MODE?: string
  readonly VITE_SIMULATED_API_DELAY_TIME?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
