import { useEffect, useRef } from "react";

import { App } from "@capacitor/app";
import { Capacitor } from "@capacitor/core";

/**
 * Makes "back" close what is open instead of leaving the app.
 *
 * There are two mechanisms because there are two shells, and only doing one of
 * them is how this shipped broken once: the History API version worked in a
 * browser tab, so it looked fixed, while the Android build still closed on the
 * first press. Capacitor does not route the hardware button through the
 * WebView's history — with no `backButton` listener registered it finishes the
 * activity — so the native path needs the plugin and the web path needs
 * history. Both end up calling the same handler.
 *
 * `layers` are ordered innermost first: a sheet closes before the screen under
 * it. A layer whose `close` does nothing swallows the press, which is how an
 * in-progress session survives a stray thumb.
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

  /** Close the innermost open layer. Returns false when nothing was open, which
   * on Android means the press should leave the app. */
  const goBack = (): boolean => {
    const top = latest.current.find((layer) => layer.open);
    if (!top) return false;
    top.close();
    return true;
  };

  // --- native shell ---
  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return;
    const handle = App.addListener("backButton", () => {
      if (!goBack()) void App.exitApp();
    });
    return () => {
      void handle.then((listener) => listener.remove());
    };
    // `goBack` reads through a ref, so the listener never needs re-registering.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- browser and installed PWA ---
  // Only armed while something is open: a permanently pushed entry would make
  // the first press on the home screen do nothing, which reads as a stuck app.
  useEffect(() => {
    if (Capacitor.isNativePlatform()) return;
    if (anyOpen && !armed.current) {
      armed.current = true;
      window.history.pushState({ ggym: true }, "");
    }
  }, [anyOpen]);

  useEffect(() => {
    if (Capacitor.isNativePlatform()) return;
    const onPop = () => {
      armed.current = false; // our sentinel is what just got popped
      goBack();
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
