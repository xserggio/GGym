import symbolSvg from "../assets/ggym-symbol.svg?raw";
import wordSvg from "../assets/ggym-word.svg?raw";
import { es } from "../i18n/es";

/**
 * Brand lockup, traced from the source artwork and split into its two pieces so
 * the same drawing can sit horizontally in the masthead and stacked on the
 * login screen.
 *
 * Both pieces are inlined (not <img>) and painted with `currentColor`: the mark
 * is ink on cement in the light theme and cement on ink in the dark one, from a
 * single file. That was the only palette that clears the contrast threshold
 * comfortably on both backgrounds — the artwork's original blue fails on the
 * dark theme (2.8 against a 3.0 minimum).
 */
interface LogoProps {
  /** Header size by default; `hero` stacks the pieces for the login screen. */
  size?: "header" | "hero";
}

const SYMBOL_RATIO = 1.65;
const WORD_RATIO = 4.11;

export function Logo({ size = "header" }: LogoProps) {
  const hero = size === "hero";

  // The wordmark is set to a fraction of the symbol so the pair keeps the
  // proportion of the original lockup at any size.
  const symbolHeight = hero ? 128 : 30;
  const wordHeight = hero ? 40 : 15;

  const piece = (markup: string, height: number, ratio: number) => (
    <span
      aria-hidden
      style={{ height, width: height * ratio, display: "block" }}
      // Inline so the paths inherit currentColor; an <img> could not be themed.
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  );

  return (
    <span
      role="img"
      aria-label={es.app.brand}
      className={`flex ${hero ? "flex-col items-center gap-3" : "items-center gap-2.5"}`}
    >
      {piece(symbolSvg, symbolHeight, SYMBOL_RATIO)}
      {piece(wordSvg, wordHeight, WORD_RATIO)}
    </span>
  );
}
