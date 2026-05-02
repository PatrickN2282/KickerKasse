/**
 * sessionStorage key used to distinguish a page reload from a fresh
 * tab-open or PWA restart.  The beforeunload handler writes this flag
 * before every unload; because sessionStorage is cleared when a tab is
 * closed (but kept across reloads), the router guard can tell whether
 * the previous unload was a reload or a real close.
 */
export const SESSION_RELOAD_FLAG_KEY = 'kicker_kasse_reloading'
export const KASSE_ROUTE_NAME = 'Kasse'
export const KASSE_LAYOUT_STORAGE_KEY = 'kasseLayout'
export const KASSE_LAYOUT_REFRESH_INTERVAL_MS = 15000
