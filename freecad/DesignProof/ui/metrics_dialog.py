# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.
"""
Metrics Dialog
==============
Quick dialog showing model complexity metrics and
the dependency structure.
"""

import FreeCAD as App
import FreeCADGui as Gui

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.dependency_analyzer import (
    analyze_dependencies, build_graph
)


def show_metrics_dialog():
    """Show a dialog with model complexity metrics."""
    doc = App.ActiveDocument
    if doc is None:
        QtWidgets.QMessageBox.warning(None, "Error", "No active document.")
        return

    analysis = analyze_dependencies(doc)
    metrics = analysis["metrics"]
    graph = analysis["graph"]

    dlg = QtWidgets.QDialog(Gui.getMainWindow())
    dlg.setWindowTitle(f"Model Metrics - {doc.Label}")
    dlg.setMinimumSize(600, 500)
    layout = QtWidgets.QVBoxLayout(dlg)

    # Metrics table
    layout.addWidget(QtWidgets.QLabel("<h3>Complexity Metrics</h3>"))

    descriptions = {
        "feature_count": "Total features (nodes in the dependency graph)",
        "edge_count": "Total dependencies (edges in the graph)",
        "average_degree": "Average connections per feature (2*E/N)",
        "max_depth": "Longest dependency chain",
        "cyclomatic_complexity": "Graph interconnection (E-N+2P). Tree=1, higher=more cross-refs",
        "graph_density": "How connected the graph is (0=sparse, 1=complete)",
        "li_entropy": "Heterogeneity of dependency structure (bits)",
    }

    m_table = QtWidgets.QTableWidget()
    m_table.setRowCount(len(metrics))
    m_table.setColumnCount(3)
    m_table.setHorizontalHeaderLabels(["Metric", "Value", "Description"])
    m_table.horizontalHeader().setStretchLastSection(True)
    m_table.setAlternatingRowColors(True)

    for i, (key, val) in enumerate(metrics.items()):
        label = key.replace("_", " ").title()
        m_table.setItem(i, 0, QtWidgets.QTableWidgetItem(label))
        m_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(val)))
        desc = descriptions.get(key, "")
        m_table.setItem(i, 2, QtWidgets.QTableWidgetItem(desc))

    m_table.resizeColumnsToContents()
    layout.addWidget(m_table)

    # Dependency list
    layout.addWidget(QtWidgets.QLabel("<h3>Feature Dependencies</h3>"))

    dep_table = QtWidgets.QTableWidget()
    nodes = list(graph.nodes.keys())
    dep_table.setRowCount(len(nodes))
    dep_table.setColumnCount(4)
    dep_table.setHorizontalHeaderLabels([
        "Feature", "Type", "Depends on", "Used by"
    ])
    dep_table.horizontalHeader().setStretchLastSection(True)
    dep_table.setAlternatingRowColors(True)

    for i, name in enumerate(nodes):
        node_info = graph.nodes[name]
        type_short = node_info["type"].split("::")[-1]
        deps = graph.dependencies_of(name)
        dependents = graph.dependents_of(name)

        dep_table.setItem(i, 0, QtWidgets.QTableWidgetItem(name))
        dep_table.setItem(i, 1, QtWidgets.QTableWidgetItem(type_short))
        dep_table.setItem(i, 2, QtWidgets.QTableWidgetItem(", ".join(deps)))
        dep_table.setItem(i, 3, QtWidgets.QTableWidgetItem(", ".join(dependents)))

        # Highlight high-dependency features
        if len(deps) + len(dependents) > 5:
            for col in range(4):
                dep_table.item(i, col).setBackground(QtGui.QColor(255, 245, 200))

    dep_table.resizeColumnsToContents()
    layout.addWidget(dep_table)

    # Close button
    close_btn = QtWidgets.QPushButton("Close")
    close_btn.clicked.connect(dlg.close)
    layout.addWidget(close_btn)

    dlg.exec()
