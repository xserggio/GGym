package com.ggym.app;

import android.os.Bundle;
import android.view.View;
import android.webkit.WebView;

import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import com.getcapacitor.BridgeActivity;

/**
 * Publishes the system bar insets to CSS.
 *
 * Android 15+ forces the activity edge to edge, so the WebView draws underneath
 * the status bar and the navigation bar. The layout reads `env(safe-area-inset-*)`
 * for that, but WebView does not always report the bottom (navigation) inset, and
 * a header or tab bar hidden behind a system bar is unusable. So the real insets
 * are measured natively and written to `--inset-*` custom properties; the
 * stylesheet takes the larger of the two sources, which is correct whether or not
 * `env()` is populated and never double-counts.
 */
public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        final WebView webView = getBridge().getWebView();
        ViewCompat.setOnApplyWindowInsetsListener(
            webView,
            (view, windowInsets) -> {
                Insets bars = windowInsets.getInsets(
                    WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.displayCutout()
                );
                float density = getResources().getDisplayMetrics().density;
                // CSS pixels, not device pixels: the WebView renders in the former.
                final String css = String.format(
                    java.util.Locale.US,
                    "document.documentElement.style.setProperty('--inset-top','%.1fpx');" +
                    "document.documentElement.style.setProperty('--inset-bottom','%.1fpx');" +
                    "document.documentElement.style.setProperty('--inset-left','%.1fpx');" +
                    "document.documentElement.style.setProperty('--inset-right','%.1fpx');",
                    bars.top / density,
                    bars.bottom / density,
                    bars.left / density,
                    bars.right / density
                );
                view.post(() -> webView.evaluateJavascript(css, null));
                return windowInsets;
            }
        );
        // Insets can arrive before the page is ready; ask for them again once it is.
        webView.setVisibility(View.VISIBLE);
        ViewCompat.requestApplyInsets(webView);
    }
}
