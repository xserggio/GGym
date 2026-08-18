import { useEffect, useRef } from "react";

/**
 * Makes the phone's back button close what is open instead of leaving the app.
 *
 * The app has no router: every screen is React state, so the WebView's history
 * was empty and Android took back to mean "close this". Rather than reach for a
 * Capacitor plugin, this drives the History API, which the native shell, the
 * installed PWA and a plain browser tab all already honour — one mechanism
 * covers the three.
 *
 * The trick is to only arm the trap while something is open. A permanently
 * pushed entry would mean the first back press on the home screen does nothing,
 * and on Android that reads as a stuck app; here back exits immediately from
 * the root, which is what everyone expects.
 *
 * `layers` are ordered innermost first — a sheet closes before the screen
 * underneath it. A layer whose `close` does nothing swallows the press, which
 * is how an in-progress session avoids being lost to a stray thumb.
 */
export interface BackLayer {
  open: boolean;
  close: () => void;
}

export function useBackButton(layers: BackLayer[]): void {
  const latest = useRef(layers);
  latest.current = layers;
  const armed = useRef(false);

  const anyOpen = layers.some((layer) => layer.open);

  useEffect(() => {
    if (anyOpen && !armed.current) {
      armed.current = true;
      window.history.pushState({ ggym: true }, "");
    }
  }, [anyOpen]);

  useEffect(() => {
    const onPop = () => {
      // Our sentinel is what just got popped; closing a layer re-arms above if
      // anything is still open.
      armed.current = false;
      const top = latest.current.find((layer) => layer.open);
      if (top) top.close();
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);
}
