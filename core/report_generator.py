"""
Report Generator
================
Genera reportes CSV y resumenes de los resultados del test
de robustez.

Uso:
    from report_generator import generate_report
    generate_report(results, params_map, metrics, output_dir)
"""

import csv
import os
from datetime import datetime


def _compute_summary(results):
    """Calcula estadisticas resumen de los resultados."""
    total = len(results)
    if total == 0:
        return {"total": 0}

    passed = sum(1 for r in results if r.status == "PASS")
    warnings = sum(1 for r in results if r.status == "WARNING")
    failed = sum(1 for r in results if r.status == "FAIL")
    success_rate = passed / total * 100

    times = [r.recompute_time for r in results if r.recompute_time > 0]
    avg_time = sum(times) / len(times) if times else 0

    # Identificar parametros mas problematicos
    # En modo OAT: usar varied_param (el parametro que realmente se vario)
    # En factorial/random: contar todos los parametros de variaciones fallidas
    param_fail_count = {}
    for r in results:
        if r.status != "FAIL":
            continue
        if r.varied_param is not None:
            # Modo OAT: solo contar el parametro variado
            param_fail_count[r.varied_param] = param_fail_count.get(r.varied_param, 0) + 1
        else:
            # Nominal o factorial/random: contar todos
            for pid in r.values:
                param_fail_count[pid] = param_fail_count.get(pid, 0) + 1

    # Features que mas fallan
    feature_fail_count = {}
    for r in results:
        for feat_name, _ in r.failed_features:
            if feat_name not in feature_fail_count:
                feature_fail_count[feat_name] = 0
            feature_fail_count[feat_name] += 1

    return {
        "total": total,
        "passed": passed,
        "warnings": warnings,
        "failed": failed,
        "success_rate": round(success_rate, 2),
        "avg_recompute_time": round(avg_time, 4),
        "param_fail_count": param_fail_count,
        "feature_fail_count": feature_fail_count,
    }


def generate_csv(results, params_map, output_path):
    """
    Genera un archivo CSV con los resultados detallados.

    Columnas: Index, Status, Volume, VolumeChange%, RecomputeTime,
              FailedFeatures, [param_1], [param_2], ...
    """
    if not results:
        return

    # Obtener lista ordenada de param_ids
    param_ids = sorted(results[0].values.keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Cabecera
        header = ["Index", "Status", "VariedParam", "Volume_mm3",
                  "VolumeChange_pct", "RecomputeTime_s",
                  "FailedFeatures", "ErrorMessage"]
        # Anadir nombres de parametros como columnas
        for pid in param_ids:
            label = params_map[pid].label if pid in params_map else pid
            header.append(label)
        writer.writerow(header)

        # Datos
        for r in results:
            failed_str = "; ".join(
                f"{name}: {detail}" for name, detail in r.failed_features
            ) if r.failed_features else ""

            varied = r.varied_param if r.varied_param else "(nominal)"
            row = [
                r.index,
                r.status,
                varied,
                round(r.volume, 2),
                round(r.volume_change_pct, 2),
                round(r.recompute_time, 4),
                failed_str,
                r.error_message,
            ]
            for pid in param_ids:
                row.append(round(r.values.get(pid, 0), 4))
            writer.writerow(row)


def generate_summary_text(summary, metrics=None):
    """Genera un texto resumen legible."""
    lines = []
    lines.append("=" * 55)
    lines.append("  ROBUSTNESS ANALYSIS REPORT")
    lines.append("=" * 55)
    lines.append(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    if summary["total"] == 0:
        lines.append("  No variations were tested.")
        return "\n".join(lines)

    # Tasa de exito
    rate = summary["success_rate"]
    lines.append(f"  Total variations:    {summary['total']}")
    lines.append(f"  Passed:              {summary['passed']}")
    lines.append(f"  Warnings:            {summary['warnings']}")
    lines.append(f"  Failed:              {summary['failed']}")
    lines.append(f"  Success rate:        {rate:.1f}%")
    lines.append(f"  Avg recompute time:  {summary['avg_recompute_time']:.4f} s")
    lines.append("")

    # Clasificacion de robustez
    if rate >= 90:
        robustness = "EXCELLENT"
    elif rate >= 70:
        robustness = "GOOD"
    elif rate >= 50:
        robustness = "MODERATE"
    elif rate >= 25:
        robustness = "POOR"
    else:
        robustness = "CRITICAL"
    lines.append(f"  Robustness rating:   {robustness}")
    lines.append("")

    # Features mas problematicos
    if summary["feature_fail_count"]:
        lines.append("  Most failing features:")
        sorted_feats = sorted(summary["feature_fail_count"].items(),
                            key=lambda x: x[1], reverse=True)
        for name, count in sorted_feats[:5]:
            pct = count / summary["failed"] * 100
            lines.append(f"    {name:25s} {count:4d} fails ({pct:.0f}%)")
        lines.append("")

    # Parametros mas asociados a fallos
    if summary["param_fail_count"]:
        lines.append("  Parameters most associated with failures:")
        sorted_params = sorted(summary["param_fail_count"].items(),
                             key=lambda x: x[1], reverse=True)
        for pid, count in sorted_params[:5]:
            pct = count / summary["failed"] * 100
            lines.append(f"    {pid:25s} {count:4d} fails ({pct:.0f}%)")
        lines.append("")

    # Metricas del modelo
    if metrics:
        lines.append("-" * 55)
        lines.append("  MODEL COMPLEXITY METRICS")
        lines.append("-" * 55)
        for key, val in metrics.items():
            label = key.replace("_", " ").title()
            lines.append(f"  {label:30s} {val}")
        lines.append("")

    lines.append("=" * 55)
    return "\n".join(lines)


def generate_report(results, params_map, output_dir, metrics=None):
    """
    Genera el reporte completo: CSV + resumen texto.

    Args:
        results: Lista de VariationResult.
        params_map: Dict {param_id: Parameter}.
        output_dir: Directorio donde guardar los archivos.
        metrics: Dict de metricas del dependency_analyzer (opcional).

    Returns:
        Dict con rutas a los archivos generados.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV detallado
    csv_path = os.path.join(output_dir, f"robustness_{timestamp}.csv")
    generate_csv(results, params_map, csv_path)

    # Resumen
    summary = _compute_summary(results)
    summary_text = generate_summary_text(summary, metrics)

    summary_path = os.path.join(output_dir, f"robustness_{timestamp}_summary.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)

    # Imprimir resumen en consola
    print(summary_text)

    return {
        "csv": csv_path,
        "summary": summary_path,
        "summary_data": summary,
    }
