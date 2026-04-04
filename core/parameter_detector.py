# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.
"""
Parameter Detector
==================
Escanea un documento FreeCAD y detecta todos los parametros
dimensionales modificables: constraints de sketches, longitudes
de extrusion, y aliases de spreadsheets.

Uso dentro de FreeCAD:
    from parameter_detector import detect_parameters
    params = detect_parameters(App.ActiveDocument)
"""

import FreeCAD as App

# Tipos de constraint que representan dimensiones modificables
DIMENSIONAL_TYPES = {
    "Distance", "DistanceX", "DistanceY",
    "Radius", "Diameter", "Angle",
}

# Propiedades de features que son longitudes modificables
EXTRUSION_PROPS = {
    "Part::Extrusion": [("LengthFwd", "mm")],
    "PartDesign::Pad": [("Length", "mm")],
    "PartDesign::Pocket": [("Length", "mm")],
    "PartDesign::Revolution": [("Angle", "deg")],
}


class Parameter:
    """Representa un parametro dimensional modificable del modelo."""

    def __init__(self, param_id, source_name, param_type, label,
                 value, unit="mm", constraint_index=None):
        self.id = param_id              # Identificador unico (ej: "Sketch.3")
        self.source_name = source_name  # Nombre del objeto FreeCAD
        self.param_type = param_type    # "sketch_constraint" o "feature_property"
        self.label = label              # Descripcion legible
        self.value = value              # Valor actual (float)
        self.unit = unit                # Unidad ("mm", "deg")
        self.constraint_index = constraint_index  # Indice si es constraint

    def __repr__(self):
        name_part = f" '{self.label}'" if self.label else ""
        return (f"Parameter({self.id}{name_part} = {self.value:.2f} {self.unit})")


def _detect_sketch_constraints(doc):
    """Detecta constraints dimensionales en todos los sketches."""
    params = []
    for obj in doc.Objects:
        if obj.TypeId != "Sketcher::SketchObject":
            continue

        for i, c in enumerate(obj.Constraints):
            if c.Type not in DIMENSIONAL_TYPES:
                continue
            if not c.Driving:
                continue  # Solo constraints "driving" (no de referencia)

            # Construir identificador unico
            param_id = f"{obj.Name}.{i}"
            # Usar el nombre del constraint si tiene, sino tipo + indice
            if c.Name:
                label = f"{obj.Label}.{c.Name}"
            else:
                label = f"{obj.Label}.{c.Type}[{i}]"

            unit = "deg" if c.Type == "Angle" else "mm"

            params.append(Parameter(
                param_id=param_id,
                source_name=obj.Name,
                param_type="sketch_constraint",
                label=label,
                value=c.Value,
                unit=unit,
                constraint_index=i,
            ))

    return params


def _detect_feature_properties(doc):
    """Detecta propiedades dimensionales en features (extrusiones, etc)."""
    params = []
    for obj in doc.Objects:
        props_to_check = EXTRUSION_PROPS.get(obj.TypeId, [])
        for prop_name, unit in props_to_check:
            if not hasattr(obj, prop_name):
                continue

            raw = getattr(obj, prop_name)
            # En FreeCAD, algunas propiedades son Quantity, otras float
            value = raw.Value if hasattr(raw, 'Value') else float(raw)

            if value == 0.0:
                continue  # Ignorar propiedades en cero (no activas)

            param_id = f"{obj.Name}.{prop_name}"
            label = f"{obj.Label}.{prop_name}"

            params.append(Parameter(
                param_id=param_id,
                source_name=obj.Name,
                param_type="feature_property",
                label=label,
                value=value,
                unit=unit,
            ))

    return params


def _detect_spreadsheet_aliases(doc):
    """Detecta aliases en spreadsheets que controlan geometria."""
    params = []
    for obj in doc.Objects:
        if obj.TypeId != "Spreadsheet::Sheet":
            continue

        # Recorrer celdas con alias
        if not hasattr(obj, 'getCellBinding'):
            continue

        try:
            aliases = obj.getPropertyByName("cells")
        except Exception:
            pass

        # Metodo alternativo: iterar propiedades dinamicas
        for prop_name in obj.PropertiesList:
            try:
                alias = obj.getAlias(prop_name)
                if alias:
                    value = getattr(obj, prop_name, None)
                    if isinstance(value, (int, float)):
                        param_id = f"{obj.Name}.{alias}"
                        params.append(Parameter(
                            param_id=param_id,
                            source_name=obj.Name,
                            param_type="spreadsheet_alias",
                            label=f"{obj.Label}.{alias}",
                            value=float(value),
                            unit="mm",  # Asumir mm, el usuario puede cambiar
                        ))
            except Exception:
                continue

    return params


def detect_parameters(doc=None):
    """
    Detecta todos los parametros dimensionales modificables del modelo.

    Args:
        doc: Documento FreeCAD. Si None, usa el documento activo.

    Returns:
        Lista de objetos Parameter.
    """
    if doc is None:
        doc = App.ActiveDocument
    if doc is None:
        raise RuntimeError("No hay documento activo en FreeCAD")

    params = []
    params.extend(_detect_sketch_constraints(doc))
    params.extend(_detect_feature_properties(doc))
    params.extend(_detect_spreadsheet_aliases(doc))

    return params


def print_parameters(params):
    """Imprime los parametros detectados en formato tabla."""
    if not params:
        print("No se detectaron parametros.")
        return

    print(f"\n{'ID':25s} | {'Label':35s} | {'Tipo':20s} | {'Valor':>10s} | Ud.")
    print("-" * 100)
    for p in params:
        print(f"{p.id:25s} | {p.label:35s} | {p.param_type:20s} | "
              f"{p.value:10.2f} | {p.unit}")
    print(f"\nTotal: {len(params)} parametros")


# Ejecucion directa en FreeCAD
if __name__ == "__main__":
    params = detect_parameters()
    print_parameters(params)
