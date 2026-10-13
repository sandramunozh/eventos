"""Cliente del servicio REST de terceros de WebApiComfamiliar (módulo Facturación).

Flujo de autenticación:
    1. POST {EXTERNAL_API_AUTH_URL} con {"Username", "Password"} (de backend/.env).
       El servicio responde con el token JWT como cadena JSON.
    2. GET {EXTERNAL_API_BASE_URL}/Facturacion/Tercero/{numero_identificacion}
       con el encabezado "Authorization: Bearer {token}".

El token se cachea en memoria hasta 60 segundos antes de su expiración (claims
del JWT) y se regenera automáticamente si el servicio responde 401.

Las credenciales viven SOLO en backend/.env (gitignored); nunca en el código
ni en el frontend.
"""
import base64
import json
import re
import threading
import time
import urllib.error
import urllib.request
from app.config import settings

_token_cache: dict = {"valor": "", "expira": 0.0}
_cache_lock = threading.Lock()


def limpiar_identificacion(valor: str) -> str:
    """Normaliza el número de identificación: sin espacios, puntos ni comas.

    El servicio externo exige el número sin separadores de miles ni caracteres
    especiales (por ejemplo 75084840 y no 75.084.840).
    """
    limpio = re.sub(r"[\s.,]", "", (valor or "").strip())
    if not re.fullmatch(r"[A-Za-z0-9\-]{4,20}", limpio):
        return ""
    return limpio


def _extraer_token(resp) -> str | None:
    """Obtiene el token de la respuesta de autenticación (string o dict)."""
    if isinstance(resp, str):
        return resp.strip() or None
    if isinstance(resp, dict):
        return (
            resp.get("token")
            or (resp.get("data") or {}).get("token")
            or resp.get("access_token")
        )
    return None


def _expiracion_del_jwt(token: str) -> float | None:
    """Lee el claim 'exp' del JWT sin validarlo (solo para cachear)."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        datos = json.loads(base64.urlsafe_b64decode(payload))
        return float(datos.get("exp") or 0)
    except (IndexError, ValueError, TypeError):
        return None


def _configurado() -> bool:
    return bool(
        settings.external_api_auth_url
        and settings.external_api_base_url
        and settings.external_api_username
        and settings.external_api_password
    )


def generar_token_externo(forzar: bool = False) -> str:
    """Genera (y cachea en memoria) el token del servicio externo.

    Reintenta una vez ante un 401 transitorio del endpoint de autenticación.
    """
    with _cache_lock:
        if (
            not forzar
            and _token_cache["valor"]
            and time.time() < _token_cache["expira"] - 60
        ):
            return _token_cache["valor"]

    if not _configurado():
        raise RuntimeError(
            "Servicio externo no configurado. Defina EXTERNAL_API_BASE_URL, "
            "EXTERNAL_API_AUTH_URL, EXTERNAL_API_USERNAME y EXTERNAL_API_PASSWORD en backend/.env."
        )

    cuerpo = json.dumps(
        {
            "Username": settings.external_api_username,
            "Password": settings.external_api_password,
        }
    ).encode()
    ultimo_error = ""
    for _intento in range(2):
        req = urllib.request.Request(
            settings.external_api_auth_url,
            data=cuerpo,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=settings.external_api_timeout) as resp:
                texto = resp.read().decode("utf-8", errors="replace")
            token = _extraer_token(json.loads(texto) if texto.strip() else None)
            if not token:
                raise RuntimeError("El servicio externo no devolvió un token válido.")
            expiracion = _expiracion_del_jwt(token)
            expira = expiracion if (expiracion and expiracion > time.time()) else time.time() + 7200
            with _cache_lock:
                _token_cache["valor"] = token
                _token_cache["expira"] = expira
            return token
        except urllib.error.HTTPError as err:
            detalle = err.read().decode("utf-8", errors="replace")[:200]
            ultimo_error = f"Autenticación con el servicio externo rechazada (HTTP {err.code}). {detalle}".strip()
            if err.code in (401, 503) and _intento == 0:
                time.sleep(1)
                continue
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            ultimo_error = f"No fue posible contactar el servicio externo: {err}"
            break
    raise RuntimeError(ultimo_error or "No fue posible generar el token del servicio externo.")


def normalizar_tercero(data) -> dict | None:
    """Lleva el objeto ``data`` al contrato camelCase documentado.

    El servicio real devuelve PascalCase (CuCod, CuNumId, ...); la documentación
    oficial usa camelCase. Se aceptan ambas formas.
    """
    if not isinstance(data, dict):
        return None
    minus = {str(clave).lower(): valor for clave, valor in data.items()}

    def campo(nombre: str):
        valor = minus.get(nombre)
        return "" if valor is None else valor

    return {
        "cuCod": campo("cucod"),
        "cuNumId": str(campo("cunumid")).strip(),
        "cuPriNom": campo("cuprinom"),
        "cuSegNom": campo("cupsegnom"),
        "cuPriApe": campo("cupriape"),
        "cuSegApe": campo("cupsegape"),
        "identificacion": campo("identificacion"),
        "tercero": campo("tercero"),
        "nomTercero": campo("nomtercero"),
    }


def consultar_tercero_externo(numero_identificacion: str) -> tuple[int, dict]:
    """Consulta el tercero en el servicio externo. Devuelve (http_status, cuerpo_json).

    Si el token expiró (401), se regenera una vez y reintenta.
    """
    base = (settings.external_api_base_url or "").rstrip("/")
    url = f"{base}/Facturacion/Tercero/{numero_identificacion}"
    for intento in (1, 2):
        try:
            token = generar_token_externo()
        except RuntimeError as err:
            return 503, {"result": -1, "message": str(err), "data": None}

        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=settings.external_api_timeout) as resp:
                cuerpo = resp.read().decode("utf-8", errors="replace")
                return resp.status, json.loads(cuerpo) if cuerpo.strip() else {}
        except urllib.error.HTTPError as err:
            cuerpo = err.read().decode("utf-8", errors="replace")
            if err.code == 401 and intento == 1:
                try:
                    generar_token_externo(forzar=True)
                except RuntimeError:
                    pass
                continue
            try:
                return err.code, json.loads(cuerpo) if cuerpo.strip() else {}
            except json.JSONDecodeError:
                return err.code, {
                    "result": -1,
                    "message": f"Respuesta no válida del servicio externo (HTTP {err.code}).",
                    "data": None,
                }
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            return 502, {
                "result": -1,
                "message": f"No fue posible contactar el servicio externo: {err}",
                "data": None,
            }
    return 502, {
        "result": -1,
        "message": "No fue posible consultar el servicio externo tras regenerar el token.",
        "data": None,
    }
