"""Consultas de trabajadores y subsidios sobre la base de datos BDMUF.

Implementa las cinco consultas del requerimiento de "Consulta de trabajadores":

1. Categoria y validacion de condiciones (VIAFILIADOSFACTURACIONDATAFONOV).
2. Grupo familiar para trabajadores (CUCODTRABAJADOR del trabajador).
3. Grupo familiar para beneficiarios (VIAFILIADOSFACTURACION: CUCOD UNION familia).
4. Subsidios otorgados el mismo dia (TBSUBESP + TBSUBESPDET, P y R separados).
5. Subsidios otorgados el mismo mes (desde el dia 1 hasta la fecha elegida).
"""
from datetime import date

from sqlalchemy import text
from app.database import engine_bdmuf

_EMPORCAJA_EXCLUIDOS = ("0.6", "0.06", "0.60", "6.00")
_SUCURSALES_EXCLUIDAS = (10, 13)


def _fila_a_dict(fila) -> dict:
    if fila is None:
        return {}
    return {clave: valor for clave, valor in fila._mapping.items()}


def _condiciones(fila: dict) -> list[dict]:
    cuclasific = str(fila.get("CUCLASIFIC") or "")
    emporcaja = str(fila.get("EMPORCAJA") or "")
    return [
        {
            "regla": "Registro de tipo trabajador (TIPO = 'T')",
            "valor": fila.get("TIPO"),
            "cumple": str(fila.get("TIPO") or "") == "T",
        },
        {
            "regla": "Tipo de contrato distinto de 'I' (TRTIPCONTR NOT IN ('I'))",
            "valor": fila.get("TRTIPCONTR"),
            "cumple": str(fila.get("TRTIPCONTR") or "") != "I",
        },
        {
            "regla": "Categoría A o B (CATTRAB IN ('A','B'))",
            "valor": fila.get("CATTRAB"),
            "cumple": str(fila.get("CATTRAB") or "") in ("A", "B"),
        },
        {
            "regla": "Sucursal distinta de 10 y 13 (SUCURSAL NOT IN (10,13))",
            "valor": fila.get("SUCURSAL"),
            "cumple": _numero(fila.get("SUCURSAL")) not in _SUCURSALES_EXCLUIDAS,
        },
        {
            "regla": "Clasificación distinta de '3' (CUCLASIFIC NOT IN ('3'))",
            "valor": fila.get("CUCLASIFIC") or "(vacio)",
            "cumple": cuclasific != "3",
        },
        {
            "regla": "% a cargo de la empresa no excluido (EMPORCAJA NOT IN ('0.6','0.06','0.60','6.00'))",
            "valor": fila.get("EMPORCAJA"),
            "cumple": emporcaja not in _EMPORCAJA_EXCLUIDOS,
        },
    ]


def _numero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def consultar_trabajador(documento: str, fecha: date | None = None) -> dict:
    fecha = fecha or date.today()
    inicio_mes = fecha.replace(day=1)

    with engine_bdmuf().connect() as con:
        consulta1 = text(
            """
            SELECT * FROM viafiliadosfacturaciondatafonov
            WHERE TIPO = 'T' AND CUNUMID = :documento AND TRTIPCONTR NOT IN ('I')
              AND CATTRAB IN ('A','B') AND SUCURSAL NOT IN (10, 13)
              AND CUCLASIFIC NOT IN ('3')
              AND EMPORCAJA NOT IN ('0.6','0.06','0.60','6.00')
            ORDER BY TIPO ASC, CATTRAB ASC
            LIMIT 1
            """
        )
        fila_condiciones = _fila_a_dict(con.execute(consulta1, {"documento": documento}).first())
        tipo_registro = "T"

        if not fila_condiciones:
            consulta_cruda = text(
                """
                SELECT * FROM viafiliadosfacturaciondatafonov
                WHERE TIPO = 'T' AND CUNUMID = :documento
                ORDER BY CATTRAB ASC
                LIMIT 1
                """
            )
            fila_condiciones = _fila_a_dict(con.execute(consulta_cruda, {"documento": documento}).first())

        if not fila_condiciones:
            consulta_beneficiario = text(
                """
                SELECT * FROM viafiliadosfacturaciondatafonov
                WHERE TIPO = 'B' AND CUNUMID = :documento
                ORDER BY LLAVE
                LIMIT 1
                """
            )
            fila_condiciones = _fila_a_dict(con.execute(consulta_beneficiario, {"documento": documento}).first())
            tipo_registro = "B"

        encontrado = bool(fila_condiciones)
        if not encontrado:
            return {
                "documento": documento,
                "fecha": fecha,
                "encontrado": False,
                "tipo_registro": "T",
                "cumple_condiciones": False,
                "trabajador": None,
                "trabajador_asociado": None,
                "condiciones": [],
                "grupo_familiar": [],
                "beneficiarios": [],
                "subsidios": {
                    "mismo_dia": {"P": 0, "R": 0},
                    "mismo_mes": {"P": 0, "R": 0},
                    "registros": [],
                },
            }

        if tipo_registro == "T":
            condiciones = _condiciones(fila_condiciones)
            cumple = all(cond["cumple"] for cond in condiciones)
            trabajador_asociado = None
        else:
            condiciones = []
            cumple = False
            consulta_trabajador_asociado = text(
                """
                SELECT * FROM viafiliadosfacturaciondatafonov
                WHERE TIPO = 'T' AND CUCOD = :cucod_trabajador
                LIMIT 1
                """
            )
            trabajador_asociado = _fila_a_dict(
                con.execute(
                    consulta_trabajador_asociado,
                    {"cucod_trabajador": _numero(fila_condiciones.get("CUCODTRABAJADOR"))},
                ).first()
            )

        cucod = _numero(fila_condiciones.get("CUCOD"))
        referencia_trabajador = _numero(fila_condiciones.get("CUCODTRABAJADOR"))
        cucod_familia = referencia_trabajador if (tipo_registro == "B" and referencia_trabajador and referencia_trabajador > 0) else cucod

        consulta_familia = text(
            """
            SELECT TIPO, CUCOD, CUNUMID, NOMBRE
            FROM viafiliadosfacturaciondatafonov
            WHERE CUCODTRABAJADOR = :cucod_familia
            """
        )
        grupo_familiar = [
            _fila_a_dict(f) for f in con.execute(consulta_familia, {"cucod_familia": cucod_familia}).fetchall()
        ]

        consulta_beneficiarios = text(
            """
            SELECT TIPO, CUCOD, CUNUMID, NOMBRE FROM viafiliadosfacturacion
            WHERE CUCOD = :cucod_familia
            UNION
            SELECT TIPO, CUCOD, CUNUMID, NOMBRE FROM viafiliadosfacturacion
            WHERE CUCODTRABAJADOR = :cucod_familia AND CUCOD <> :cucod_familia
            """
        )
        beneficiarios = [
            _fila_a_dict(f) for f in con.execute(consulta_beneficiarios, {"cucod_familia": cucod_familia}).fetchall()
        ]

        params = {"cucod": cucod, "fecha": fecha, "inicio_mes": inicio_mes}
        base_subsidios = text(
            """
            FROM tbsubesp A
            JOIN tbsubespdet B ON (B.TBSUBESP_ID = A.ID)
            WHERE B.USR_CUCODB = :cucod
              AND A.TIPO_VENTA IN ('P','R')
              AND A.AUCODESTAD = 'A'
              AND A.FECHA BETWEEN :inicio_mes AND :fecha
            """
        )
        conteos: dict = {("dia", "P"): 0, ("dia", "R"): 0, ("mes", "P"): 0, ("mes", "R"): 0}
        consulta_conteos = text(
            "SELECT (A.FECHA = :fecha) AS es_dia, A.TIPO_VENTA, COUNT(*) AS n " + str(base_subsidios) +
            " GROUP BY es_dia, A.TIPO_VENTA"
        )
        for fila in con.execute(consulta_conteos, params).fetchall():
            tipo_venta = fila.TIPO_VENTA
            conteos[("mes", tipo_venta)] += int(fila.n)
            if fila.es_dia:
                conteos[("dia", tipo_venta)] += int(fila.n)

        consulta_registros = text(
            """
            SELECT B.ID AS registro, A.FECHA AS fecha, A.TIPO_VENTA AS tipo_venta,
                   A.VALOR_TAR AS valor_tar, A.VALOR_DES AS valor_des,
                   A.PORCENTAJE AS porcentaje, A.USR_CATE AS categoria,
                   A.USR_GRUPO AS grupo, A.VOUCHER AS voucher,
                   (A.FECHA = :fecha) AS mismo_dia
            """ + str(base_subsidios) + " ORDER BY A.FECHA DESC, B.ID DESC LIMIT 200"
        )
        registros = [_fila_a_dict(f) for f in con.execute(consulta_registros, params).fetchall()]

    return {
        "documento": documento,
        "fecha": fecha,
        "encontrado": True,
        "tipo_registro": tipo_registro,
        "cumple_condiciones": cumple,
        "trabajador": fila_condiciones,
        "trabajador_asociado": trabajador_asociado,
        "condiciones": condiciones,
        "grupo_familiar": grupo_familiar,
        "beneficiarios": beneficiarios,
        "subsidios": {
            "mismo_dia": {"P": conteos[("dia", "P")], "R": conteos[("dia", "R")]},
            "mismo_mes": {"P": conteos[("mes", "P")], "R": conteos[("mes", "R")]},
            "registros": registros,
        },
    }
