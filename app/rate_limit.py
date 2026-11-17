import time
from collections import defaultdict

MAX_INTENTOS = 5
VENTANA_SEGUNDOS = 300
BLOQUEO_SEGUNDOS = 300

_fallos: dict[str, list[float]] = defaultdict(list)
_bloqueados: dict[str, float] = {}


def esta_bloqueado(ip: str) -> int:
    """Segundos que faltan de bloqueo (0 si no está bloqueada)."""
    hasta = _bloqueados.get(ip)
    if hasta is None:
        return 0
    restante = int(hasta - time.time())
    if restante <= 0:
        del _bloqueados[ip]
        _fallos.pop(ip, None)
        return 0
    return restante


def registrar_fallo(ip: str) -> bool:
    """Anota un fallo. Devuelve True si con este fallo la IP queda bloqueada."""
    ahora = time.time()
    recientes = [t for t in _fallos[ip] if ahora - t < VENTANA_SEGUNDOS]
    recientes.append(ahora)
    _fallos[ip] = recientes
    if len(recientes) >= MAX_INTENTOS:
        _bloqueados[ip] = ahora + BLOQUEO_SEGUNDOS
        return True
    return False


def limpiar(ip: str) -> None:
    """Borra los fallos de una IP (se usa cuando inicia sesión bien)."""
    _fallos.pop(ip, None)