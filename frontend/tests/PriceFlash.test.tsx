import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { PriceFlash } from "@/components/PriceFlash";

const fmt = (n: number) => n.toFixed(2);

describe("PriceFlash", () => {
  it("renders the formatted value, no flash on first render", () => {
    const { container } = render(
      <PriceFlash value={190.5} direction="flat" seq={1} format={fmt} />
    );
    const span = container.querySelector("span")!;
    expect(span).toHaveTextContent("190.50");
    expect(span.className).not.toMatch(/flash-/);
  });

  it("applies flash-up when a new up tick arrives", () => {
    const { container, rerender } = render(
      <PriceFlash value={190.5} direction="flat" seq={1} format={fmt} />
    );
    rerender(<PriceFlash value={191.0} direction="up" seq={2} format={fmt} />);
    expect(container.querySelector("span")!.className).toMatch(/flash-up/);
  });

  it("applies flash-down on a down tick", () => {
    const { container, rerender } = render(
      <PriceFlash value={190.5} direction="flat" seq={1} format={fmt} />
    );
    rerender(<PriceFlash value={189.0} direction="down" seq={2} format={fmt} />);
    expect(container.querySelector("span")!.className).toMatch(/flash-down/);
  });

  it("shows an em-dash when value is null", () => {
    const { container } = render(
      <PriceFlash value={null} direction="flat" seq={0} format={fmt} />
    );
    expect(container.querySelector("span")!).toHaveTextContent("—");
  });
});
