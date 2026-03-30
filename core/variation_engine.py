"""
Variation Engine
================
Genera combinaciones de valores de parametros para testear
la robustez del modelo. Soporta tres modos:

- OAT (One-At-a-Time): varia cada parametro independientemente
- Factorial: todas las combinaciones posibles
- Muestreo aleatorio: subconjunto aleatorio del espacio factorial

Uso:
    from variation_engine import generate_variations, ParameterRange
    ranges = [
        ParameterRange("Sketch.3", 10, 50, steps=5),
        ParameterRange("Extrude.LengthFwd", 20, 100, steps=5),
    ]
    variations = generate_variations(ranges, mode="oat")
"""

import itertools
import random


class ParameterRange:
    """Define el rango de variacion de un parametro."""

    def __init__(self, param_id, min_val, max_val, steps=5, unit="mm"):
        if min_val >= max_val:
            raise ValueError(f"min ({min_val}) debe ser menor que max ({max_val})")
        if steps < 2:
            raise ValueError(f"steps ({steps}) debe ser >= 2")

        self.param_id = param_id
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.steps = int(steps)
        self.unit = unit

    @property
    def values(self):
        """Genera la lista de valores discretos para este parametro."""
        if self.steps == 1:
            return [self.min_val]
        step_size = (self.max_val - self.min_val) / (self.steps - 1)
        return [self.min_val + i * step_size for i in range(self.steps)]

    @property
    def nominal(self):
        """Valor central del rango (punto medio)."""
        return (self.min_val + self.max_val) / 2.0

    def __repr__(self):
        return (f"ParameterRange({self.param_id}: "
                f"{self.min_val}-{self.max_val}, {self.steps} steps)")


def _generate_oat(ranges, nominal_values=None):
    """
    One-At-a-Time: varia un parametro mientras los demas quedan fijos
    en su valor nominal.

    Genera N1 + N2 + ... + Nk - k + 1 variaciones (incluyendo el nominal).
    Mucho mas rapido que factorial para espacios grandes.

    Cada variacion es un dict con los valores Y una clave especial
    "_varied_param" que indica que parametro se vario (None para el nominal).
    """
    if not ranges:
        return []

    # Valores nominales: punto medio de cada rango, o los proporcionados
    if nominal_values is None:
        nominal_values = {r.param_id: r.nominal for r in ranges}

    variations = []

    # Variacion nominal (todos en punto medio)
    nominal = dict(nominal_values)
    nominal["_varied_param"] = None
    variations.append(nominal)

    # Para cada parametro, variar solo ese
    for r in ranges:
        for val in r.values:
            if abs(val - nominal_values[r.param_id]) < 1e-9:
                continue  # Saltar el valor nominal (ya incluido)
            variation = dict(nominal_values)
            variation[r.param_id] = val
            variation["_varied_param"] = r.param_id
            variations.append(variation)

    return variations


def _generate_factorial(ranges):
    """
    Factorial completo: todas las combinaciones N1 x N2 x ... x Nk.
    Puede ser muy grande — usar con precaucion.
    """
    if not ranges:
        return []

    all_values = [r.values for r in ranges]
    param_ids = [r.param_id for r in ranges]

    variations = []
    for combo in itertools.product(*all_values):
        variation = {pid: val for pid, val in zip(param_ids, combo)}
        variations.append(variation)

    return variations


def _generate_random(ranges, n_samples=100, seed=42):
    """
    Muestreo aleatorio: selecciona n_samples combinaciones al azar
    del espacio factorial. Util cuando el factorial es demasiado grande.
    """
    if not ranges:
        return []

    rng = random.Random(seed)
    all_values = [r.values for r in ranges]
    param_ids = [r.param_id for r in ranges]

    # Si el factorial completo es mas pequeno que n_samples, devolver todo
    total_factorial = 1
    for r in ranges:
        total_factorial *= r.steps
    if total_factorial <= n_samples:
        return _generate_factorial(ranges)

    # Generar combinaciones unicas aleatorias
    seen = set()
    variations = []
    max_attempts = n_samples * 10
    attempts = 0

    while len(variations) < n_samples and attempts < max_attempts:
        combo = tuple(rng.choice(vals) for vals in all_values)
        if combo not in seen:
            seen.add(combo)
            variation = {pid: val for pid, val in zip(param_ids, combo)}
            variations.append(variation)
        attempts += 1

    return variations


def generate_variations(ranges, mode="oat", n_samples=100, seed=42,
                        nominal_values=None):
    """
    Genera variaciones de parametros segun el modo seleccionado.

    Args:
        ranges: Lista de ParameterRange.
        mode: "oat", "factorial", o "random".
        n_samples: Numero de muestras para modo "random".
        seed: Semilla para reproducibilidad en modo "random".
        nominal_values: Dict {param_id: valor} para OAT. Si None, usa
                       el punto medio de cada rango.

    Returns:
        Lista de dicts {param_id: valor} con cada variacion.
    """
    if not ranges:
        return []

    if mode == "oat":
        variations = _generate_oat(ranges, nominal_values)
    elif mode == "factorial":
        variations = _generate_factorial(ranges)
    elif mode == "random":
        variations = _generate_random(ranges, n_samples, seed)
    else:
        raise ValueError(f"Modo desconocido: '{mode}'. Usar 'oat', 'factorial' o 'random'.")

    return variations


def estimate_space_size(ranges, mode="factorial"):
    """
    Estima el tamano del espacio de variaciones sin generarlas.
    Util para advertir al usuario antes de lanzar un factorial grande.
    """
    if mode == "oat":
        return sum(r.steps for r in ranges) - len(ranges) + 1
    elif mode == "factorial":
        size = 1
        for r in ranges:
            size *= r.steps
        return size
    elif mode == "random":
        return min(100, estimate_space_size(ranges, "factorial"))
    return 0


def print_variation_summary(ranges, mode="factorial"):
    """Imprime un resumen del espacio de variaciones."""
    size = estimate_space_size(ranges, mode)
    print(f"\nModo: {mode}")
    print(f"Parametros: {len(ranges)}")
    for r in ranges:
        print(f"  {r.param_id}: {r.min_val} -> {r.max_val} "
              f"({r.steps} pasos)")
    print(f"Total variaciones: {size}")
    if mode == "factorial" and size > 500:
        print(f"  AVISO: Espacio grande ({size}). "
              f"Considerar modo 'oat' ({estimate_space_size(ranges, 'oat')}) "
              f"o 'random'.")
