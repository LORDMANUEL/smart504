from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    read_only: bool
    required_roles: frozenset[str]


class ToolRegistry:
    def __init__(self, tools: list[ToolDefinition]) -> None:
        self.tools = tuple(tools)
        names = [tool.name for tool in self.tools]
        if len(names) != len(set(names)):
            raise ValueError("Tool names must be unique")

    def names(self) -> tuple[str, ...]:
        return tuple(tool.name for tool in self.tools)

    def allowed_for(self, role: str) -> tuple[ToolDefinition, ...]:
        normalized = role.strip().casefold()
        return tuple(tool for tool in self.tools if normalized in tool.required_roles)


def build_default_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            ToolDefinition(
                name="list_overdue_work_orders",
                description="Lista órdenes de trabajo atrasadas y su responsable.",
                read_only=True,
                required_roles=frozenset({"advisor", "supervisor", "manager", "admin"}),
            ),
            ToolDefinition(
                name="get_vehicle_history",
                description="Consulta historial técnico por VIN, placa o vehículo.",
                read_only=True,
                required_roles=frozenset({"advisor", "technician", "supervisor", "manager", "admin"}),
            ),
            ToolDefinition(
                name="search_parts",
                description="Busca repuestos, precio y existencia disponible sin reservar ni consumir.",
                read_only=True,
                required_roles=frozenset({"advisor", "technician", "warehouse", "supervisor", "manager", "admin"}),
            ),
            ToolDefinition(
                name="get_workshop_kpis",
                description="Consulta indicadores agregados de taller y rentabilidad.",
                read_only=True,
                required_roles=frozenset({"supervisor", "manager", "admin"}),
            ),
        ]
    )
