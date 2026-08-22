from krita import *
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QMessageBox
import math
import os


class GridExporter(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction(
            "grid_exporter_export",
            "Export Grid Cells",
            "tools/scripts",
        )
        action.triggered.connect(self.export_grid)

    def export_grid(self):
        doc = Krita.instance().activeDocument()

        if doc is None:
            self._error("No active document.")
            return

        if not doc.fileName():
            self._error(
                "Please save the current .kra file first.\n\n"
                "The PNGs will be created beside the .kra file."
            )
            return

        grid = doc.gridConfig()

        # The script cuts rectangular image areas from a rectangular grid.
        # Isometric grids are intentionally not supported.
        if grid.type() not in ("rectangular", "rectangle"):
            self._error(
                "The current grid is not rectangular.\n\n"
                f"Krita reports grid type: {grid.type()}\n\n"
                "Please set Grid Type to Rectangular."
            )
            return

        spacing = grid.spacing()
        offset = grid.offset()

        sx = int(spacing.x())
        sy = int(spacing.y())
        ox = int(offset.x())
        oy = int(offset.y())

        if sx <= 0 or sy <= 0:
            self._error(f"Invalid grid spacing: {sx} × {sy}px.")
            return

        width = int(doc.width())
        height = int(doc.height())

        # Rectangular grid lines are:
        #   x = offset_x + n * spacing_x
        #   y = offset_y + n * spacing_y
        #
        # Find the grid line at or immediately before document coordinate 0.
        first_x = ox - math.ceil(ox / sx) * sx
        first_y = oy - math.ceil(oy / sy) * sy

        x_lines = [0]
        x = first_x
        while x < width:
            px = int(round(x))
            if 0 < px < width:
                x_lines.append(px)
            x += sx
        x_lines.append(width)
        x_lines = sorted(set(x_lines))

        y_lines = [0]
        y = first_y
        while y < height:
            py = int(round(y))
            if 0 < py < height:
                y_lines.append(py)
            y += sy
        y_lines.append(height)
        y_lines = sorted(set(y_lines))

        if len(x_lines) < 2 or len(y_lines) < 2:
            self._error("No grid cells were found inside the document.")
            return

        output_dir = os.path.splitext(doc.fileName())[0] + "_grid_export"
        os.makedirs(output_dir, exist_ok=True)

        # rootNode() represents the whole layer tree. Its projection respects
        # layer visibility, group composition, blending, masks, etc.
        root = doc.rootNode()

        # Krita documents that are already saved/exported with the desired
        # normal PNG settings can be exported using an empty InfoObject;
        # Krita then uses the format defaults.
        export_config = InfoObject()

        exported = 0
        failed = 0

        for row in range(len(y_lines) - 1):
            y0 = y_lines[row]
            y1 = y_lines[row + 1]

            for col in range(len(x_lines) - 1):
                x0 = x_lines[col]
                x1 = x_lines[col + 1]

                cell_w = x1 - x0
                cell_h = y1 - y0

                if cell_w <= 0 or cell_h <= 0:
                    continue

                filename = os.path.join(
                    output_dir,
                    f"grid_r{row + 1:03d}_c{col + 1:03d}.png",
                )

                ok = root.save(
                    filename,
                    doc.xRes(),
                    doc.yRes(),
                    export_config,
                    QRect(x0, y0, cell_w, cell_h),
                )

                if ok:
                    exported += 1
                else:
                    failed += 1

        QMessageBox.information(
            Krita.instance().activeWindow(),
            "Grid Cell Exporter",
            (
                "Grid export finished.\n\n"
                f"Grid spacing: {sx} × {sy}px\n"
                f"Grid offset: {ox}, {oy}px\n"
                f"Canvas: {width} × {height}px\n"
                f"Exported: {exported}\n"
                f"Failed: {failed}\n\n"
                f"Output folder:\n{output_dir}"
            ),
        )

    def _error(self, message):
        QMessageBox.critical(
            Krita.instance().activeWindow(),
            "Grid Cell Exporter",
            message,
        )


Krita.instance().addExtension(GridExporter(Krita.instance()))
