"use client";

import { useEffect, useRef, useState } from "react";
import type { Direction } from "@/lib/types";

interface Props {
  value: number | null;
  direction: Direction;
  /** cambia en cada tick para re-disparar el destello aunque el precio repita */
  seq: number;
  format: (n: number) => string;
  className?: string;
}

/**
 * Celda de precio que destella verde/rojo al cambiar. Aplica una clase CSS con
 * transición y la quita tras ~500ms (misma duración que la animación).
 */
export function PriceFlash({ value, direction, seq, format, className = "" }: Props) {
  const [flash, setFlash] = useState("");
  const first = useRef(true);

  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    if (direction === "flat") return;
    setFlash(direction === "up" ? "flash-up" : "flash-down");
    const t = setTimeout(() => setFlash(""), 500);
    return () => clearTimeout(t);
    // seq cambia en cada tick recibido
  }, [seq, direction]);

  return (
    <span className={`tnum rounded px-1 ${flash} ${className}`}>
      {value == null ? "—" : format(value)}
    </span>
  );
}
