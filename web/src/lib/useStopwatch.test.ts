// @vitest-environment jsdom
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useStopwatch } from "./useStopwatch";

/** Paused time must never reach the stored duration: the treadmill number is
 * used for the calorie estimate, so counting a water break would inflate it. */
describe("useStopwatch", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("counts only the time it was running", () => {
    const { result } = renderHook(() => useStopwatch());

    act(() => result.current.start());
    act(() => void vi.advanceTimersByTime(30_000));
    expect(result.current.seconds).toBe(30);

    act(() => result.current.pause());
    act(() => void vi.advanceTimersByTime(60_000)); // paused: does not count
    expect(result.current.seconds).toBe(30);
    expect(result.current.paused).toBe(true);
    expect(result.current.running).toBe(false);

    act(() => result.current.resume());
    act(() => void vi.advanceTimersByTime(10_000));
    expect(result.current.seconds).toBe(40);

    let saved: { durationS: number } | null = null;
    act(() => {
      saved = result.current.stop();
    });
    expect(saved!.durationS).toBe(40);
  });

  it("can be stopped while paused", () => {
    const { result } = renderHook(() => useStopwatch());
    act(() => result.current.start());
    act(() => void vi.advanceTimersByTime(15_000));
    act(() => result.current.pause());

    let saved: { durationS: number } | null = null;
    act(() => {
      saved = result.current.stop();
    });
    expect(saved!.durationS).toBe(15);
    expect(result.current.running).toBe(false);
    expect(result.current.paused).toBe(false);
    expect(result.current.seconds).toBe(0);
  });

  it("stores nothing when stopped before a second elapsed", () => {
    const { result } = renderHook(() => useStopwatch());
    act(() => result.current.start());
    let saved: unknown = "unset";
    act(() => {
      saved = result.current.stop();
    });
    expect(saved).toBeNull();
  });
});
