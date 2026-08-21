from __future__ import annotations

import os

import chromadb

DOCUMENTS = [
    ("workflow-ot", "Flujo de orden de trabajo", "La OT pasa por creada, cotizada por tecnico, pendiente de aprobacion, pendiente de repuestos, lista para facturar y facturada. Ningun trabajo adicional se ejecuta sin aprobacion."),
    ("safety-brakes", "Seguridad de frenos", "Si el vehiculo pierde frenos o no frena, debe detenerse en un lugar seguro y solicitar asistencia. No debe continuar conduciendo."),
    ("fitment", "Compatibilidad de repuestos", "La compatibilidad se valida por VIN, marca, modelo, ano, motor y version antes de instalar. El catalogo demo incluye Ford Escape 2020, Ford F-150 2020 y Honda Civic 2008."),
    ("appointments", "Reservas del taller", "El cliente puede solicitar una cita desde la landing. El taller confirma disponibilidad, fecha y alcance inicial antes de recibir el vehiculo."),
    ("privacy", "Privacidad del cliente", "El asistente publico no revela ordenes, facturas, vehiculos ni datos personales sin autenticacion. La IA no registra pagos ni modifica inventario."),
]


def main() -> None:
    raw_url = os.getenv("CHROMA_URL", "http://chromadb:8000").split("://", 1)[-1]
    host, _, port = raw_url.partition(":")
    client = chromadb.HttpClient(host=host or "chromadb", port=int(port or "8000"))
    collection = client.get_or_create_collection(
        os.getenv("CHROMA_COLLECTION", "smartdiag_knowledge")
    )
    collection.upsert(
        ids=[item[0] for item in DOCUMENTS],
        metadatas=[{"title": item[1]} for item in DOCUMENTS],
        documents=[item[2] for item in DOCUMENTS],
    )
    print(f"seeded={len(DOCUMENTS)} collection={collection.name}")


if __name__ == "__main__":
    main()
