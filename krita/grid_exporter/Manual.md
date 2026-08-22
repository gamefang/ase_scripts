# Grid Cell Exporter

Use **Tools > Scripts > Export Grid Cells**.

The plugin:

- reads the active document's rectangular grid spacing and offset;
- exports one PNG for every grid cell intersecting the canvas;
- uses the current visible layer composition;
- ignores hidden layers;
- does not modify or crop the source `.kra`;
- writes PNGs beside the `.kra` in `<document-name>_grid_export`;
- uses an empty `InfoObject`, so the PNG exporter uses Krita's default export configuration.

Only rectangular grids are supported. Isometric grids are not exported because their cells are not rectangular image regions.
