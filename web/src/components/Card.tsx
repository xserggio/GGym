import type { HTMLAttributes } from "react";

/** Paper surface with a 1px hairline border and the constant 10px radius. */
export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...props}
      className={`bg-paper border border-line rounded-card ${className}`}
    />
  );
}
