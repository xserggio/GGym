import { useState } from "react";

/**
 * Exercise thumbnail. Loads exercises/<slug>.webp (public/, duotone-processed)
 * and falls back to the prototype's hatched marker when the image is missing —
 * so exercises without a picture still lay out correctly.
 */
interface ExerciseThumbProps {
  name: string;
  exerciseId?: string;
  size?: number;
}

export function ExerciseThumb({ name, exerciseId, size = 64 }: ExerciseThumbProps) {
  const [failed, setFailed] = useState(false);
  const src = exerciseId ? `${import.meta.env.BASE_URL}exercises/${exerciseId}.webp` : null;
  const showImg = src !== null && !failed;
  return (
    <div
      aria-hidden
      style={{
        width: size,
        height: size,
        borderRadius: 8,
        flex: "none",
        boxSizing: "border-box",
        overflow: "hidden",
        padding: showImg ? 0 : 5,
        border: "1px solid var(--line)",
        background:
          "repeating-linear-gradient(135deg, var(--thumbA) 0 3px, var(--thumbB) 3px 6px)",
        display: "flex",
        alignItems: "flex-end",
      }}
    >
      {showImg ? (
        <img
          src={src}
          alt=""
          loading="lazy"
          onError={() => setFailed(true)}
          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
        />
      ) : (
        <span className="font-mono text-[7px] leading-[1.15] text-gris">
          {name.slice(0, 14)}
        </span>
      )}
    </div>
  );
}
