import { useState } from "react";

import { BarbellChart } from "./components/BarbellChart";
import { Button } from "./components/Button";
import { Card } from "./components/Card";
import { NumberStepper } from "./components/NumberStepper";
import { es } from "./i18n/es";
import { numEs } from "./lib/format";

type Tema = "clara" | "oscura";

const SAMPLE_WEIGHTS = [60, 82.5, 100, 140];

/**
 * Design-system preview. Not a product screen — a scratch page to eyeball the
 * tokens and primitives against the prototype while the real screens (Hoy,
 * Sesión activa) are built next.
 */
export function App() {
  const [tema, setTema] = useState<Tema>("clara");
  const [weight, setWeight] = useState(82.5);
  const [reps, setReps] = useState(8);

  return (
    <div data-tema={tema} className="min-h-full bg-bg text-ink">
      <div className="mx-auto flex max-w-[390px] flex-col gap-6 px-4 py-8">
        <header className="flex items-baseline gap-3">
          <span className="font-display text-2xl">{es.app.title}</span>
          <div className="ml-auto flex gap-1.5">
            <Button
              variant="ghost"
              onClick={() => setTema("clara")}
              className="!min-h-0 !px-2 !py-1"
            >
              clara
            </Button>
            <Button
              variant="ghost"
              onClick={() => setTema("oscura")}
              className="!min-h-0 !px-2 !py-1"
            >
              oscura
            </Button>
          </div>
        </header>

        <section className="flex flex-col gap-3">
          <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
            barra cargada
          </div>
          {SAMPLE_WEIGHTS.map((w) => (
            <Card key={w} className="flex items-center gap-3 p-3">
              <BarbellChart weightKg={w} />
              <span className="font-mono text-sm tabular-nums">
                {numEs(w)} {es.units.kg}
              </span>
            </Card>
          ))}
        </section>

        <section className="flex flex-col gap-3">
          <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
            fila de serie
          </div>
          <Card className="flex items-center gap-3 p-3">
            <NumberStepper
              label={es.session.weight}
              value={weight}
              step={2.5}
              onChange={setWeight}
            />
            <NumberStepper
              label={es.session.reps}
              value={reps}
              step={1}
              min={1}
              onChange={setReps}
              valueWidth={34}
            />
            <div className="ml-auto flex flex-col items-center gap-1">
              <BarbellChart weightKg={weight} compact />
            </div>
          </Card>
        </section>

        <section className="flex flex-col gap-2">
          <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
            botones
          </div>
          <Button variant="primary" className="w-full">
            {es.actions.start}
          </Button>
          <Button variant="secondary" className="w-full">
            {es.actions.endSession}
          </Button>
        </section>
      </div>
    </div>
  );
}
