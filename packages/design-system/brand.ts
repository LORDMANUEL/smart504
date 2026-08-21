export const SMARTDIAG_BRAND = {
  name: "SmartDiag504",
  tagline: "Diagnóstico preciso. Servicio transparente.",
  descriptor: "Diagnóstico, reparación y repuestos con trazabilidad por vehículo.",
  locale: "es-HN",
  currency: "HNL",
  colors: {
    navy: "#071827",
    blue: "#0878d1",
    cyan: "#17a9c2",
    amber: "#d89a24",
    white: "#ffffff",
  },
  voice: {
    precise: true,
    transparent: true,
    technicalWithoutBeingCold: true,
  },
} as const;

export type SmartDiagBrand = typeof SMARTDIAG_BRAND;
