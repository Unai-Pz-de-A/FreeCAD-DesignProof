"""
Recompute Tester
================
Modulo critico: aplica variaciones parametricas al modelo,
regenera, detecta fallos, y restaura el estado original.

SIEMPRE trabaja sobre una copia del archivo .FCStd para
proteger el modelo original del usuario.

Uso:
    from recompute_tester import RobustnessTester
    tester = RobustnessTester(doc)
    results = tester.run(variations, params_map)
"""

import FreeCAD as App
import os
import shutil
import time


class VariationResult:
    """Resultado de una variacion individual."""

    def __init__(self, index, values):
        self.index = index
        self.varied_param = values.pop("_varied_param", None)  # OAT: que parametro se vario
        self.values = values            # {param_id: valor}
        self.success = False
        self.shape_valid = False
        self.volume = 0.0
        self.failed_features = []       # [(name, error_detail)]
        self.recompute_time = 0.0       # Segundos
        self.error_message = ""
        self.volume_change_pct = 0.0    # Cambio de volumen vs nominal

    @property
    def status(self):
        if self.success and self.shape_valid:
            return "PASS"
        elif self.success and not self.shape_valid:
            return "WARNING"  # Regenero pero shape invalida
        else:
            return "FAIL"

    def __repr__(self):
        return f"VariationResult(#{self.index} {self.status})"


class RobustnessTester:
    """
    Motor principal de test de robustez.

    Aplica variaciones parametricas, regenera el modelo,
    y registra exitos/fallos.
    """

    def __init__(self, doc=None):
        if doc is None:
            doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No hay documento activo")
        self.doc = doc
        self._nominal_volume = None
        self._cancelled = False
        self._pre_invalid = set()  # Features ya invalidos antes de empezar

    def _record_pre_existing_errors(self):
        """
        Registra features que ya estan en estado Invalid ANTES
        de aplicar cualquier variacion. Estos se excluyen del
        analisis de robustez.
        """
        self._pre_invalid = set()
        for obj in self.doc.Objects:
            if hasattr(obj, 'State') and 'Invalid' in str(obj.State):
                self._pre_invalid.add(obj.Name)
        if self._pre_invalid:
            print(f"  AVISO: {len(self._pre_invalid)} feature(s) ya invalido(s) "
                  f"antes del test: {', '.join(self._pre_invalid)}")
            print(f"  Estos se excluiran del analisis de fallos.")

    def _get_final_shape(self):
        """Obtiene el Shape del ultimo objeto valido del modelo."""
        for obj in reversed(self.doc.Objects):
            if hasattr(obj, 'Shape') and not obj.Shape.isNull():
                return obj
        return None

    def _save_original_values(self, params_map):
        """Guarda los valores originales de todos los parametros."""
        originals = {}
        for param_id, param in params_map.items():
            if param.param_type == "sketch_constraint":
                obj = self.doc.getObject(param.source_name)
                if obj and param.constraint_index is not None:
                    originals[param_id] = obj.Constraints[param.constraint_index].Value
            elif param.param_type == "feature_property":
                obj = self.doc.getObject(param.source_name)
                prop_name = param_id.split(".")[-1]
                if obj and hasattr(obj, prop_name):
                    raw = getattr(obj, prop_name)
                    originals[param_id] = raw.Value if hasattr(raw, 'Value') else float(raw)
        return originals

    def _apply_values(self, values, params_map):
        """
        Aplica un conjunto de valores de parametros al modelo.
        Aplica parametro por parametro, registrando errores individuales
        en vez de abortar todo si uno falla.
        """
        errors = []
        for param_id, value in values.items():
            if param_id.startswith("_"):
                continue  # Saltar metadata (_varied_param, etc)
            try:
                param = params_map[param_id]

                if param.param_type == "sketch_constraint":
                    obj = self.doc.getObject(param.source_name)
                    if obj is None:
                        errors.append(f"{param_id}: objeto no encontrado")
                        continue
                    unit = "deg" if param.unit == "deg" else "mm"
                    obj.setDatum(param.constraint_index,
                               App.Units.Quantity(value, unit))

                elif param.param_type == "feature_property":
                    obj = self.doc.getObject(param.source_name)
                    if obj is None:
                        errors.append(f"{param_id}: objeto no encontrado")
                        continue
                    prop_name = param_id.split(".")[-1]
                    setattr(obj, prop_name, App.Units.Quantity(value, "mm"))

            except Exception as e:
                errors.append(f"{param_id}: {type(e).__name__}: {e}")

        return errors

    def _check_recompute(self):
        """
        Regenera el modelo y verifica el resultado.
        Solo reporta features que se vuelven Invalid DESPUES de la
        variacion (excluye los que ya estaban rotos antes).
        """
        t0 = time.time()
        self.doc.recompute()
        recompute_time = time.time() - t0

        # Detectar features NUEVAMENTE invalidos (no pre-existentes)
        # Nota: en headless, Sketches con MapMode attachment al Origin
        # quedan ['Touched', 'Invalid'] tras setDatum incluso si el
        # modelo regenera correctamente. Solo ignoramos 'Invalid' para
        # Sketches con Shape valido; para features no-Sketch (Pad, Pocket,
        # Fillet...) un 'Invalid' es un fallo real.
        new_failures = []
        for obj in self.doc.Objects:
            if not hasattr(obj, 'State'):
                continue
            if 'Invalid' in str(obj.State) and obj.Name not in self._pre_invalid:
                # Sketches en headless: ignorar si Shape sigue valido
                # (bug de attachment al Origin en FreeCADcmd)
                if 'Sketcher' in obj.TypeId:
                    if hasattr(obj, 'Shape') and not obj.Shape.isNull() and obj.Shape.isValid():
                        continue
                new_failures.append((obj.Name, f"State={obj.State}"))

        # Verificar shape del resultado final
        final_obj = self._get_final_shape()
        shape_valid = False
        volume = 0.0

        if final_obj is not None:
            try:
                shape_valid = final_obj.Shape.isValid()
                volume = final_obj.Shape.Volume
            except Exception as e:
                new_failures.append(
                    (final_obj.Name, f"Shape error: {e}")
                )

        # Criterio de exito: sin nuevos fallos Y shape valida Y volumen > 0
        success = (len(new_failures) == 0) and shape_valid and (volume > 0)

        return success, new_failures, shape_valid, volume, recompute_time

    def cancel(self):
        """Permite cancelar el test desde otro hilo (ej: GUI)."""
        self._cancelled = True

    def run(self, variations, params_map, callback=None):
        """
        Ejecuta el test de robustez completo.

        Args:
            variations: Lista de dicts {param_id: valor} generadas
                       por variation_engine.
            params_map: Dict {param_id: Parameter} de parameter_detector.
            callback: Funcion(index, total, result) llamada tras cada
                     variacion. Util para barras de progreso.

        Returns:
            Lista de VariationResult.
        """
        self._cancelled = False
        results = []
        total = len(variations)

        # Recompute inicial para revelar errores latentes (ej: Origin
        # no cargado en headless que hace que Sketches attached fallen)
        self.doc.recompute()

        # Registrar features ya invalidos antes de empezar
        self._record_pre_existing_errors()

        # Guardar valores originales
        originals = self._save_original_values(params_map)

        # Obtener volumen nominal
        final_obj = self._get_final_shape()
        if final_obj is not None:
            try:
                self._nominal_volume = final_obj.Shape.Volume
            except Exception:
                self._nominal_volume = None

        # Optimizacion OAT: detectar cuando cambia el parametro variado
        # para evitar restaurar+recomputar entre pasos del mismo parametro
        prev_varied = "__first__"

        for i, variation in enumerate(variations):
            if self._cancelled:
                break

            result = VariationResult(index=i, values=dict(variation))
            curr_varied = variation.get("_varied_param")

            try:
                # En OAT, solo restaurar al nominal cuando cambiamos
                # de parametro (no entre pasos del mismo parametro)
                if curr_varied != prev_varied and prev_varied != "__first__":
                    self._apply_values(originals, params_map)
                    self.doc.recompute()

                # 1. Aplicar valores (con manejo de errores por parametro)
                apply_errors = self._apply_values(variation, params_map)
                if apply_errors:
                    result.error_message = "; ".join(apply_errors)

                # 2. Regenerar y verificar (siempre, incluso con errores parciales)
                (result.success, result.failed_features,
                 result.shape_valid, result.volume,
                 result.recompute_time) = self._check_recompute()

                # 3. Calcular cambio de volumen
                if self._nominal_volume and self._nominal_volume > 0 and result.volume > 0:
                    result.volume_change_pct = (
                        (result.volume - self._nominal_volume)
                        / self._nominal_volume * 100
                    )

            except Exception as e:
                result.success = False
                result.error_message = f"Fatal: {type(e).__name__}: {e}"

            results.append(result)
            prev_varied = curr_varied

            if callback:
                callback(i, total, result)

        # Restaurar valores originales al terminar
        try:
            self._apply_values(originals, params_map)
            self.doc.recompute()
        except Exception:
            pass

        return results


def create_working_copy(original_path):
    """Crea una copia del archivo .FCStd para trabajar sin riesgo."""
    base, ext = os.path.splitext(original_path)
    copy_path = f"{base}_robustness_test{ext}"
    shutil.copy2(original_path, copy_path)
    return copy_path


def cleanup_working_copy(copy_path):
    """Elimina la copia de trabajo si existe."""
    if os.path.exists(copy_path):
        os.remove(copy_path)


def run_on_copy(original_path, variations, params_map, callback=None):
    """
    Ejecuta el test sobre una copia del modelo, protegiendo el original.
    Solo funciona dentro de FreeCAD (necesita App.openDocument).

    Args:
        original_path: Ruta al .FCStd original.
        variations: Lista de variaciones.
        params_map: Dict {param_id: Parameter}.
        callback: Funcion de progreso.

    Returns:
        Lista de VariationResult.
    """
    copy_path = create_working_copy(original_path)
    try:
        copy_doc = App.openDocument(copy_path)
        App.setActiveDocument(copy_doc.Name)

        # Re-detectar parametros en la copia (mismos IDs, distinto doc)
        tester = RobustnessTester(copy_doc)
        results = tester.run(variations, params_map, callback=callback)

        App.closeDocument(copy_doc.Name)
        return results
    finally:
        cleanup_working_copy(copy_path)
