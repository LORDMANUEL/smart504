export type SeasonalThemeCode = 'NONE' | 'JANUARY_NEW_YEAR' | 'FEBRUARY_FRIENDSHIP' | 'MARCH_MAINTENANCE' | 'APRIL_ROAD_SAFETY' | 'MAY_FAMILY' | 'JUNE_ENVIRONMENT' | 'JULY_TRAVEL' | 'AUGUST_WORKSHOP' | 'PATRIA_SEPTEMBER' | 'OCTOBER_PREVENTION' | 'NOVEMBER_SAVINGS' | 'DECEMBER_HOLIDAYS';

export const seasonalThemes: Record<Exclude<SeasonalThemeCode, 'NONE'>, { title: string; message: string; symbol: string }> = {
  JANUARY_NEW_YEAR: { title: 'Nuevo año, vehículo al día', message: 'Comience el año con mantenimiento preventivo y decisiones claras.', symbol: '✦' },
  FEBRUARY_FRIENDSHIP: { title: 'Cuidamos lo que le acompaña', message: 'Seguridad y confianza para cada viaje.', symbol: '♥' },
  MARCH_MAINTENANCE: { title: 'Mes del mantenimiento', message: 'Prevenir cuesta menos que reparar una falla mayor.', symbol: '⚙' },
  APRIL_ROAD_SAFETY: { title: 'Seguridad en carretera', message: 'Frenos, llantas y luces listos antes de viajar.', symbol: '◆' },
  MAY_FAMILY: { title: 'Viajes que cuidan a la familia', message: 'Revisión preventiva para llegar con tranquilidad.', symbol: '♥' },
  JUNE_ENVIRONMENT: { title: 'Eficiencia que cuida el ambiente', message: 'Un motor afinado consume mejor y contamina menos.', symbol: '●' },
  JULY_TRAVEL: { title: 'Temporada de viaje', message: 'Prepare su vehículo antes de salir a carretera.', symbol: '➜' },
  AUGUST_WORKSHOP: { title: 'Tecnología y oficio', message: 'Diagnóstico con evidencia, experiencia y trazabilidad.', symbol: '⚙' },
  PATRIA_SEPTEMBER: { title: 'Septiembre, mes de la patria', message: 'Honduras y Centroamérica: trabajo, identidad y futuro.', symbol: '★' },
  OCTOBER_PREVENTION: { title: 'Octubre de prevención', message: 'Detectar a tiempo protege su vehículo y su presupuesto.', symbol: '✚' },
  NOVEMBER_SAVINGS: { title: 'Oportunidades de noviembre', message: 'Promociones claras en servicios y repuestos seleccionados.', symbol: '%' },
  DECEMBER_HOLIDAYS: { title: 'Viajes seguros en diciembre', message: 'Revise su vehículo antes de compartir el camino.', symbol: '✦' },
};
