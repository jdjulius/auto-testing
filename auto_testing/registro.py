"""Registro incremental de escenarios de prueba y de ejecuciones en CSV.

- ``escenarios.csv``: catálogo de escenarios. Cada prueba nueva que pytest
  descubre se agrega con el siguiente ID (ESC-0001, ESC-0002, ...). Las
  existentes nunca se duplican: solo se actualizan su último estado y sus
  contadores.
- ``ejecuciones.csv``: historial; se agrega una fila por escenario en cada
  corrida, sin reescribir las anteriores.
"""

from __future__ import annotations

import csv
import os
import re
import tempfile
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path

PREFIJO_ID = "ESC-"


@dataclass
class Escenario:
    id: str
    nodeid: str
    modulo: str
    funcionalidad: str
    descripcion: str
    resultado_esperado: str
    prioridad: str
    fecha_alta: str
    navegador: str = ""
    ultimo_estado: str = "NO_EJECUTADO"
    ultima_ejecucion: str = ""
    ejecuciones: int = 0
    fallos: int = 0


@dataclass
class Ejecucion:
    run_id: str
    fecha: str
    escenario_id: str
    nodeid: str
    estado: str
    duracion_s: float
    mensaje: str = ""


COLUMNAS_ESCENARIOS = [f.name for f in fields(Escenario)]
COLUMNAS_EJECUCIONES = [f.name for f in fields(Ejecucion)]


_SEPARADORES = re.compile(r"\s*[,;]\s*")


def texto_csv(valor):
    """Deja el texto listo para un CSV sin comillas: la coma es solo el separador.

    Las comas y los punto y coma del texto pasan a ' - ' (Excel en español usa
    ';' como separador), las comillas dobles a simples y los saltos de línea a
    espacios.
    """
    if not isinstance(valor, str):
        return valor
    valor = valor.replace("\r", " ").replace("\n", " ").replace('"', "'")
    return _SEPARADORES.sub(" - ", valor)


def ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


class RegistroEscenarios:
    def __init__(self, ruta_escenarios: Path, ruta_ejecuciones: Path) -> None:
        self.ruta_escenarios = Path(ruta_escenarios)
        self.ruta_ejecuciones = Path(ruta_ejecuciones)
        self.escenarios: dict[str, Escenario] = {}
        self.nuevos: list[Escenario] = []
        self._cargar()

    # ------------------------------------------------------------------ CSV
    def _cargar(self) -> None:
        if not self.ruta_escenarios.exists():
            return
        with self.ruta_escenarios.open(newline="", encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                fila["ejecuciones"] = int(fila.get("ejecuciones") or 0)
                fila["fallos"] = int(fila.get("fallos") or 0)
                datos = {c: fila.get(c, "") for c in COLUMNAS_ESCENARIOS}
                esc = Escenario(**datos)
                self.escenarios[esc.nodeid] = esc

    def guardar(self) -> None:
        """Reescribe el catálogo de forma atómica (archivo temporal + rename).

        Los textos se guardan sin comas para que la coma sea solo el separador,
        y se genera además ``escenarios.xlsx`` para abrirlo en Excel."""
        self.ruta_escenarios.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            dir=self.ruta_escenarios.parent, prefix=".escenarios", suffix=".tmp"
        )
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNAS_ESCENARIOS)
            writer.writeheader()
            for esc in sorted(self.escenarios.values(), key=lambda e: e.id):
                writer.writerow({k: texto_csv(v) for k, v in asdict(esc).items()})
        os.replace(tmp, self.ruta_escenarios)
        self._guardar_excel()

    def _guardar_excel(self) -> None:
        """Copia del catálogo en .xlsx, que Excel abre bien en cualquier idioma."""
        try:
            from auto_testing.excel import exportar_excel
        except ImportError:  # openpyxl no instalado: solo se genera el CSV
            return
        exportar_excel(
            self.ruta_escenarios.with_suffix(".xlsx"),
            [{k: texto_csv(v) for k, v in asdict(e).items()}
             for e in sorted(self.escenarios.values(), key=lambda e: e.id)],
        )

    def agregar_ejecuciones(self, ejecuciones: list[Ejecucion]) -> None:
        """Agrega filas al historial sin tocar las existentes."""
        if not ejecuciones:
            return
        self.ruta_ejecuciones.parent.mkdir(parents=True, exist_ok=True)
        nuevo = not self.ruta_ejecuciones.exists() or self.ruta_ejecuciones.stat().st_size == 0
        with self.ruta_ejecuciones.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNAS_EJECUCIONES)
            if nuevo:
                writer.writeheader()
            for ej in ejecuciones:
                writer.writerow(asdict(ej))

    # ------------------------------------------------------------ escenarios
    def _siguiente_id(self) -> str:
        numeros = [
            int(m.group(1))
            for e in self.escenarios.values()
            if (m := re.fullmatch(rf"{PREFIJO_ID}(\d+)", e.id))
        ]
        return f"{PREFIJO_ID}{max(numeros, default=0) + 1:04d}"

    def registrar(
        self,
        nodeid: str,
        *,
        id: str | None = None,
        modulo: str = "",
        funcionalidad: str = "",
        descripcion: str = "",
        resultado_esperado: str = "",
        prioridad: str = "Media",
        navegador: str = "",
    ) -> Escenario:
        """Da de alta el escenario si es nuevo; si ya existe, refresca su
        documentación (descripción, módulo, etc.) sin alterar su ID ni historial."""
        existente = self.escenarios.get(nodeid)
        if existente:
            for campo, valor in {
                "modulo": modulo,
                "funcionalidad": funcionalidad,
                "descripcion": descripcion,
                "resultado_esperado": resultado_esperado,
                "prioridad": prioridad,
                "navegador": navegador,
            }.items():
                if valor:
                    setattr(existente, campo, valor)
            return existente

        ids_usados = {e.id for e in self.escenarios.values()}
        if id and id in ids_usados:
            raise ValueError(f"ID de escenario duplicado: {id} ({nodeid})")
        esc = Escenario(
            id=id or self._siguiente_id(),
            nodeid=nodeid,
            modulo=modulo,
            funcionalidad=funcionalidad,
            descripcion=descripcion,
            resultado_esperado=resultado_esperado,
            prioridad=prioridad,
            fecha_alta=ahora(),
            navegador=navegador,
        )
        self.escenarios[nodeid] = esc
        self.nuevos.append(esc)
        return esc

    def registrar_resultado(self, nodeid: str, estado: str, fecha: str) -> Escenario:
        esc = self.escenarios[nodeid]
        esc.ultimo_estado = estado
        esc.ultima_ejecucion = fecha
        esc.ejecuciones += 1
        if estado in ("FALLIDO", "ERROR"):
            esc.fallos += 1
        return esc
