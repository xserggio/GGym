/**
 * Placeholder for the exercise photo (real images come later). Reproduces the
 * prototype's hatched marker so layouts read correctly meanwhile. The slug hints
 * which image belongs here.
 */
interface ExerciseThumbProps {
  name: string;
  size?: number;
}

export function ExerciseThumb({ name, size = 64 }: ExerciseThumbProps) {
  return (
    <div
      aria-hidden
      style={{
        width: size,
        height: size,
        borderRadius: 8,
        flex: "none",
        boxSizing: "border-box",
        padding: 5,
        border: "1px solid var(--line)",
        background:
          "repeating-linear-gradient(135deg, var(--thumbA) 0 3px, var(--thumbB) 3px 6px)",
        display: "flex",
        alignItems: "flex-end",
      }}
    >
      <span className="font-mono text-[7px] leading-[1.15] text-gris">
        {name.slice(0, 14)}
      </span>
    </div>
  );
}
