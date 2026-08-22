from krita import *
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QImage, QColor
from PyQt5.QtWidgets import (
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QDialogButtonBox,
    QLabel,
)
import math
import os

#region CONFIG
# Developers only need to maintain this SETTINGS dict.
# Each key becomes a runtime setting with: default, name (dialog label), tip (tooltip).
# Optional 'type': 'str' | 'bool' | 'int'  (inferred from default if omitted)

SCRIPT_NAME = 'Grid Cell Exporter'
SCRIPT_SHOW_NAME = 'Export Grid Cells'
SETTINGS_GROUP = 'GridExporter'

SETTINGS = {
    'OUTPUT_DIR_SUFFIX': {
        'default': '_grid',
        'name': 'Output folder suffix:',
        'tip': 'Folder name is: <kra_basename><suffix>',
    },
    'SKIP_EMPTY_CELLS': {
        'default': True,
        'name': 'Skip empty cells',
        'tip': 'Skip cells that are fully transparent or a single solid color.',
    },
    'EMPTY_ALPHA_THRESHOLD': {
        'default': 0,
        'name': 'Empty alpha threshold:',
        'tip': 'Alpha <= this value counts as transparent (0-255).',
        'type': 'int',
        'min': 0,
        'max': 255,
    },
    'LIST_OUTPUT_FILENAMES': {
        'default': '',
        'name': 'Output filenames (csv):',
        'tip': (
            'Comma-separated names, e.g. dog,cat,fish.\n'
            'Used in export order; missing entries fall back to 1, 2, 3...'
        ),
    },
}
#endregion


class GridExporter(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        # Runtime values; filled from defaults then kritarc / dialog
        self.cfg = {}
        self._init_cfg_from_defaults()

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction(
            'grid_exporter_export',
            SCRIPT_SHOW_NAME,
            'tools',
        )
        action.triggered.connect(self.export_grid)

    def _parent_widget(self):
        win = Krita.instance().activeWindow()
        if win is None:
            return None
        try:
            return win.qwindow()
        except Exception:
            return None

    #region SETTINGS
    def _init_cfg_from_defaults(self):
        """Seed self.cfg from SETTINGS defaults."""
        self.cfg = {}
        for key, meta in SETTINGS.items():
            self.cfg[key] = meta['default']

    def _setting_type(self, key):
        meta = SETTINGS[key]
        if 'type' in meta:
            return meta['type']
        val = meta['default']
        if isinstance(val, bool):
            return 'bool'
        if isinstance(val, int) and not isinstance(val, bool):
            return 'int'
        return 'str'

    def _load_settings(self):
        """Load settings from kritarc into self.cfg."""
        app = Krita.instance()
        for key, meta in SETTINGS.items():
            default = meta['default']
            raw = app.readSetting(SETTINGS_GROUP, key, None)
            if raw is None or raw == '':
                self.cfg[key] = default
                continue
            kind = self._setting_type(key)
            if kind == 'bool':
                self.cfg[key] = raw.lower() in ('true', '1', 'yes')
            elif kind == 'int':
                try:
                    self.cfg[key] = int(raw)
                except ValueError:
                    self.cfg[key] = default
            else:
                self.cfg[key] = raw

    def _save_settings(self):
        """Persist self.cfg to kritarc."""
        app = Krita.instance()
        for key in SETTINGS:
            val = self.cfg[key]
            kind = self._setting_type(key)
            if kind == 'bool':
                text = 'true' if val else 'false'
            else:
                text = str(val)
            app.writeSetting(SETTINGS_GROUP, key, text)

    def _show_settings_dialog(self):
        """
        Show settings dialog built from SETTINGS.
        Returns True on OK (cfg + kritarc updated), False on Cancel.
        """
        self._load_settings()

        dlg = QDialog(self._parent_widget())
        dlg.setWindowTitle(SCRIPT_NAME + ' — Settings')
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        widgets = {}

        for key, meta in SETTINGS.items():
            kind = self._setting_type(key)
            tip = meta.get('tip', '')

            if kind == 'bool':
                w = QCheckBox(meta['name'])
                w.setChecked(bool(self.cfg[key]))
                if tip:
                    w.setToolTip(tip)
                form.addRow(w)
            elif kind == 'int':
                w = QSpinBox()
                w.setRange(meta.get('min', 0), meta.get('max', 99999))
                w.setValue(int(self.cfg[key]))
                if tip:
                    w.setToolTip(tip)
                form.addRow(meta['name'], w)
            else:
                w = QLineEdit(str(self.cfg[key]))
                if tip:
                    w.setToolTip(tip)
                form.addRow(meta['name'], w)

            widgets[key] = (w, kind)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec_() != QDialog.Accepted:
            return False

        for key, (w, kind) in widgets.items():
            if kind == 'bool':
                self.cfg[key] = w.isChecked()
            elif kind == 'int':
                self.cfg[key] = int(w.value())
            else:
                self.cfg[key] = w.text().strip()

        # Keep a sensible fallback for empty suffix
        if not self.cfg.get('OUTPUT_DIR_SUFFIX'):
            self.cfg['OUTPUT_DIR_SUFFIX'] = SETTINGS['OUTPUT_DIR_SUFFIX']['default']

        self._save_settings()
        return True

    def _filename_list(self):
        """Parse LIST_OUTPUT_FILENAMES into a list of stripped non-empty names."""
        raw = self.cfg.get('LIST_OUTPUT_FILENAMES', '') or ''
        return [part.strip() for part in raw.split(',') if part.strip()]
    #endregion

    #region MAIN
    def export_grid(self):
        # Settings dialog first; cancel aborts export
        if not self._show_settings_dialog():
            return

        app = Krita.instance()
        doc = app.activeDocument()

        if doc is None:
            self._error('No active document.')
            return

        if not doc.fileName():
            self._error(
                'Please save the current .kra file first.\n\n'
                'The PNGs will be created beside the .kra file.'
            )
            return

        grid = doc.gridConfig()

        # The script cuts rectangular image areas from a rectangular grid.
        # Isometric grids are intentionally not supported.
        if grid.type() not in ('rectangular', 'rectangle'):
            self._error(
                'The current grid is not rectangular.\n\n'
                'Krita reports grid type: {}\n\n'
                'Please set Grid Type to Rectangular.'.format(grid.type())
            )
            return

        spacing = grid.spacing()
        offset = grid.offset()

        sx = int(spacing.x())
        sy = int(spacing.y())
        ox = int(offset.x())
        oy = int(offset.y())

        if sx <= 0 or sy <= 0:
            self._error('Invalid grid spacing: {} × {}px.'.format(sx, sy))
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
            self._error('No grid cells were found inside the document.')
            return

        suffix = self.cfg['OUTPUT_DIR_SUFFIX']
        output_dir = os.path.splitext(doc.fileName())[0] + suffix
        os.makedirs(output_dir, exist_ok=True)

        # rootNode() represents the whole layer tree. Its projection respects
        # layer visibility, group composition, blending, masks, etc.
        root = doc.rootNode()

        # Ensure projection is up to date before reading pixels / exporting
        try:
            doc.refreshProjection()
            doc.waitForDone()
        except Exception:
            pass

        # Empty InfoObject -> Krita uses format defaults for PNG
        export_config = InfoObject()

        # Prevent popups
        old_app_batch = app.batchmode()
        old_doc_batch = doc.batchmode()
        try:
            app.setBatchmode(True)
            doc.setBatchmode(True)
        except Exception:
            pass

        exported = 0
        failed = 0
        skipped = 0
        cell_index = 0
        name_list = self._filename_list()
        skip_empty = bool(self.cfg['SKIP_EMPTY_CELLS'])

        try:
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

                    cell_index += 1

                    # Check empty (transparent or uniform solid color)
                    if skip_empty and self._is_empty_cell(doc, x0, y0, cell_w, cell_h):
                        skipped += 1
                        continue

                    # Named list first; fall back to sequential number
                    list_pos = exported  # next export slot in name_list
                    if list_pos < len(name_list):
                        base_name = name_list[list_pos]
                    else:
                        base_name = str(cell_index)

                    filename = os.path.join(output_dir, base_name + '.png')

                    # Node.save() often returns False even when the file is written.
                    # Prefer checking the output file after the call.
                    root.save(
                        filename,
                        doc.xRes(),
                        doc.yRes(),
                        export_config,
                        QRect(x0, y0, cell_w, cell_h),
                    )

                    if os.path.isfile(filename) and os.path.getsize(filename) > 0:
                        exported += 1
                    else:
                        failed += 1
        finally:
            # Revert settings
            try:
                app.setBatchmode(old_app_batch)
                doc.setBatchmode(old_doc_batch)
            except Exception:
                pass

        QMessageBox.information(
            self._parent_widget(),
            SCRIPT_NAME,
            (
                'Grid export finished.\n\n'
                'Grid spacing: {} × {}px\n'
                'Grid offset: {}, {}px\n'
                'Canvas: {} × {}px\n'
                'Exported: {}\n'
                'Skipped (empty): {}\n'
                'Failed: {}\n\n'
                'Output folder:\n{}'
            ).format(
                sx, sy, ox, oy, width, height,
                exported, skipped, failed, output_dir,
            ),
        )
    #endregion

    def _is_empty_cell(self, doc, x, y, w, h):
        """
        True if the cell has no real content:
        - every pixel alpha <= EMPTY_ALPHA_THRESHOLD, or
        - every pixel is the exact same color (solid fill / pure black plate).
        Uses Document.projection() (QImage) for reliable composite data.
        On failure, returns False so the cell is still exported.
        """
        try:
            img = doc.projection(x, y, w, h)
            if img is None or img.isNull():
                return True

            # Normalize to a format with alpha we can sample easily
            if img.format() != QImage.Format_ARGB32:
                img = img.convertToFormat(QImage.Format_ARGB32)

            first = img.pixel(0, 0)
            all_same = True
            all_transparent = True
            thresh = int(self.cfg.get('EMPTY_ALPHA_THRESHOLD', 0))

            for py in range(img.height()):
                for px in range(img.width()):
                    c = img.pixel(px, py)
                    a = (c >> 24) & 0xFF
                    if a > thresh:
                        all_transparent = False
                    if c != first:
                        all_same = False
                    if not all_transparent and not all_same:
                        return False

            return all_transparent or all_same
        except Exception:
            return False

    def _error(self, message):
        QMessageBox.critical(
            self._parent_widget(),
            SCRIPT_NAME,
            message,
        )


Krita.instance().addExtension(GridExporter(Krita.instance()))