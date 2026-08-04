import { describe, expect, it } from "vitest";

import { BAR_KG, platesPerSide } from "./barbell";

const kgs = (total: number, bar?: number) =>
  platesPerSide(total, bar).map((p) => p.kg);

describe("platesPerSide", () => {
  it("returns nothing for an empty or sub-bar weight", () => {
    expect(kgs(BAR_KG)).toEqual([]);
    expect(kgs(15)).toEqual([]);
    expect(kgs(0)).toEqual([]);
  });

  it("loads a single pair", () => {
    expect(kgs(60)).toEqual([20]); // (60-20)/2 = 20 per side
    expect(kgs(40)).toEqual([10]);
  });

  it("greedy-fills largest plate first", () => {
    expect(kgs(100)).toEqual([25, 15]); // 40 per side
    expect(kgs(140)).toEqual([25, 25, 10]); // 60 per side
  });

  it("handles fractional plates without float drift", () => {
    // 82,5 kg -> 31,25 per side -> 25 + 5 + 1,25
    expect(kgs(82.5)).toEqual([25, 5, 1.25]);
    // 62,5 kg -> 21,25 per side -> 20 + 1,25
    expect(kgs(62.5)).toEqual([20, 1.25]);
  });

  it("respects a custom bar (e.g. machines with barKg=0)", () => {
    expect(kgs(140, 0)).toEqual([25, 25, 20]); // 70 per side
    expect(kgs(45, 0)).toEqual([20, 2.5]); // 22,5 per side
  });
});
