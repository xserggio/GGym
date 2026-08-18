import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const VARIANTS: Record<Variant, string> = {
  primary: "bg-blue text-paper border border-transparent font-display text-xl",
  secondary: "bg-transparent text-ink border border-line",
  ghost: "bg-transparent text-blue border border-line font-mono text-xs",
};

/**
 * All touch targets are at least 44px tall (CLAUDE.md).
 *
 * Colour here is a signal, not decoration: blue marks what responds to a tap,
 * the same blue the bottom nav uses for the destination you are on. Static text
 * never takes it, so the cue stays reliable.
 */
export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  return (
    <button
      {...props}
      className={`min-h-touch rounded-card px-4 leading-none disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
    />
  );
}
