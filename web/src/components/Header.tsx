import type { ReactNode } from "react";

interface HeaderProps {
  /** Small mono line above the title (context, not chrome). */
  eyebrow?: string;
  /** Screen title. Ignored when `brand` is given. */
  title?: string;
  /** Wordmark, used on the home screen instead of a redundant title. */
  brand?: ReactNode;
  /** Right-hand slot, usually a ghost button. */
  action?: ReactNode;
  /** Back arrow slot, shown at the left edge. */
  leading?: ReactNode;
}

/**
 * Masthead, not a toolbar.
 *
 * It sits on the paper surface, one step lighter than the content below, which
 * separates it without a heavy border or any colour. The title is optically
 * centred — absolutely positioned sides rather than a flex row, so it stays on
 * the axis of the screen whatever sits beside it — and set in the brand face,
 * the same one as the wordmark. The home screen is the exception: there the
 * wordmark itself leads, from the left, as a masthead does.
 */
export function Header({ eyebrow, title, brand, action, leading }: HeaderProps) {
  return (
    <header
      className="sticky top-0 z-10 border-b border-line bg-paper px-3 pb-2"
      style={{ paddingTop: "calc(0.625rem + var(--safe-top))" }}
    >
      <div className="relative flex min-h-[38px] items-center">
        {leading && <div className="absolute left-0 z-10">{leading}</div>}

        {brand ? (
          /* The wordmark is its own mark: centred, and with no rule under it —
             that accent exists to give a plain title some weight, which a logo
             does not need. */
          <div className="mx-auto flex items-center">{brand}</div>
        ) : (
          <div className="mx-auto flex min-w-0 max-w-[62%] flex-col items-center px-2">
            {eyebrow && (
              <div className="truncate font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                {eyebrow}
              </div>
            )}
            <h1 className="truncate font-brand text-[23px] font-semibold uppercase leading-[1.1] tracking-[0.12em]">
              {title}
            </h1>
            <div className="mt-1 h-[2px] w-7 bg-ink" />
          </div>
        )}

        {action && <div className="absolute right-0 z-10">{action}</div>}
      </div>
    </header>
  );
}
