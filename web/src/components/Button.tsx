import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const VARIANTS: Record<Variant, string> = {
  primary: "bg-blue text-paper border border-transparent font-display text-xl",
  secondary: "bg-transparent text-ink border border-line",
  ghost: "bg-transparent text-gris border border-line font-mono text-xs",
};

/** All touch targets are at least 44px tall (CLAUDE.md). */
export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  return (
    <button
      {...props}
      className={`min-h-touch rounded-card px-4 leading-none disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
    />
  );
}
