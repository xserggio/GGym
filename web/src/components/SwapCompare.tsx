import { BottomSheet } from "./BottomSheet";
import { ExerciseThumb } from "./ExerciseThumb";
import { es } from "../i18n/es";
import { equipmentLabel, patternLabel } from "../lib/labels";

/** Kit that fixes the path of the movement for you. */
const GUIDED = ["maquina", "polea"];

interface SwapCompareProps {
  detail: Record<string, string>;
  /** The finding's own reason, already written out by the caller. */
  why: string;
  onClose: () => void;
}

/**
 * Side by side, with the difference spelled out.
 *
 * Swapping an exercise is the assistant's most opinionated move: it changes
 * what she does in the gym, not just how many sets. Asking her to accept that
 * from a one-line label is asking for trust she has no way to check, so this
 * shows both exercises and says exactly what is being traded — the movement
 * stays, the tool changes — and why.
 */
export function SwapCompare({ detail, why, onClose }: SwapCompareProps) {
  const guidedAfter = GUIDED.includes(detail.to_equipment ?? "");
  const guidedBefore = GUIDED.includes(detail.from_equipment ?? "");
  const restBefore = Number(detail.from_rest_s ?? 0);
  const restAfter = Number(detail.to_rest_s ?? 0);

  const changes = [
    detail.pattern ? es.assistant.compareSamePattern(patternLabel(detail.pattern)) : null,
    detail.from_equipment && detail.to_equipment
      ? es.assistant.compareEquipment(
          equipmentLabel(detail.from_equipment),
          equipmentLabel(detail.to_equipment),
        )
      : null,
    guidedAfter && !guidedBefore
      ? es.assistant.compareGuided
      : guidedBefore && !guidedAfter
        ? es.assistant.compareFree
        : null,
    restBefore && restAfter
      ? restBefore - restAfter >= 30
        ? es.assistant.compareDemandLess
        : es.assistant.compareDemandSame
      : null,
  ].filter(Boolean) as string[];

  const side = (label: string, name: string, id: string, equipment: string) => (
    <div className="flex-1">
      <div className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.16em] text-gris">
        {label}
      </div>
      <ExerciseThumb name={name} exerciseId={id} size={148} />
      <div className="mt-2 text-[15px] leading-snug">{name}</div>
      <div className="text-[12px] text-gris">{equipmentLabel(equipment)}</div>
    </div>
  );

  return (
    <BottomSheet title={es.assistant.compareTitle} onClose={onClose}>
      <div className="flex items-start gap-3">
        {side(
          es.assistant.compareNow,
          detail.exercise ?? "",
          detail.from_id ?? "",
          detail.from_equipment ?? "",
        )}
        <div className="pt-9 font-mono text-[18px] text-gris">→</div>
        {side(
          es.assistant.compareProposed,
          detail.replacement ?? "",
          detail.to_id ?? "",
          detail.to_equipment ?? "",
        )}
      </div>

      <section className="mt-5">
        <h3 className="font-display text-[19px] leading-tight">
          {es.assistant.compareWhatChanges}
        </h3>
        <ul className="mt-2 flex flex-col gap-2">
          {changes.map((line) => (
            <li key={line} className="flex gap-2.5">
              <span
                className="mt-[8px] h-1.5 w-1.5 shrink-0 rounded-full"
                style={{ background: "var(--blue-text)" }}
              />
              <span className="text-[14px] leading-snug">{line}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-5">
        <h3 className="font-display text-[19px] leading-tight">
          {es.assistant.compareWhyTitle}
        </h3>
        <p className="mt-2 text-[14px] leading-snug text-gris">{why}</p>
      </section>

      <button
        type="button"
        onClick={onClose}
        className="mt-5 h-touch w-full rounded-card border border-line text-sm"
      >
        {es.assistant.compareClose}
      </button>
    </BottomSheet>
  );
}
