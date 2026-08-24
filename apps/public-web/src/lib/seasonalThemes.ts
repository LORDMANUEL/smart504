export type SeasonalThemeCode = 'NONE' | 'JANUARY_NEW_YEAR' | 'FEBRUARY_FRIENDSHIP' | 'MARCH_MAINTENANCE' | 'APRIL_ROAD_SAFETY' | 'MAY_FAMILY' | 'JUNE_ENVIRONMENT' | 'JULY_TRAVEL' | 'AUGUST_WORKSHOP' | 'PATRIA_SEPTEMBER' | 'OCTOBER_PREVENTION' | 'NOVEMBER_SAVINGS' | 'DECEMBER_HOLIDAYS';

export type SeasonalThemeDefinition = {
  title: string;
  message: string;
  symbol: string;
  shortLabel: string;
};

export const seasonalThemes: Record<Exclude<SeasonalThemeCode, 'NONE'>, SeasonalThemeDefinition> = {
  JANUARY_NEW_YEAR: { title: 'Nuevo año, vehículo al día', message: 'Comience el año con mantenimiento preventivo y decisiones claras.', symbol: '✦', shortLabel: 'Nuevo año' },
  FEBRUARY_FRIENDSHIP: { title: 'Cuidamos lo que le acompaña', message: 'Seguridad y confianza para cada viaje.', symbol: '♥', shortLabel: 'Mes de la confianza' },
  MARCH_MAINTENANCE: { title: 'Mes del mantenimiento', message: 'Prevenir cuesta menos que reparar una falla mayor.', symbol: '⚙', shortLabel: 'Mantenimiento' },
  APRIL_ROAD_SAFETY: { title: 'Seguridad en carretera', message: 'Frenos, llantas y luces listos antes de viajar.', symbol: '◆', shortLabel: 'Seguridad vial' },
  MAY_FAMILY: { title: 'Viajes que cuidan a la familia', message: 'Revisión preventiva para llegar con tranquilidad.', symbol: '♥', shortLabel: 'Mes de la familia' },
  JUNE_ENVIRONMENT: { title: 'Eficiencia que cuida el ambiente', message: 'Un motor afinado consume mejor y contamina menos.', symbol: '●', shortLabel: 'Eficiencia' },
  JULY_TRAVEL: { title: 'Temporada de viaje', message: 'Prepare su vehículo antes de salir a carretera.', symbol: '➜', shortLabel: 'Viajes seguros' },
  AUGUST_WORKSHOP: { title: 'Tecnología y oficio', message: 'Diagnóstico con evidencia, experiencia y trazabilidad.', symbol: '⚙', shortLabel: 'Mes del taller' },
  PATRIA_SEPTEMBER: { title: 'Septiembre, mes de la patria', message: 'Celebramos Honduras con servicio, trabajo e identidad.', symbol: '★', shortLabel: 'Honduras, mes de la patria' },
  OCTOBER_PREVENTION: { title: 'Octubre de prevención', message: 'Detectar a tiempo protege su vehículo y su presupuesto.', symbol: '✚', shortLabel: 'Prevención automotriz' },
  NOVEMBER_SAVINGS: { title: 'Noviembre de oportunidades', message: 'Ahorro real en servicios y repuestos seleccionados.', symbol: '%', shortLabel: 'Promociones verificadas' },
  DECEMBER_HOLIDAYS: { title: 'Viajes seguros en diciembre', message: 'Prepare su vehículo antes de compartir el camino.', symbol: '✦', shortLabel: 'Temporada de viaje' },
};
