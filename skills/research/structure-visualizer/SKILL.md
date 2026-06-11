---
name: structure-visualizer
description: "Render atomic/molecular structures as publication-quality PNG images. Use this skill whenever the user asks to visualize, render, display, or draw atomic structures, molecules, crystal structures, slabs, surfaces, POSCAR, CONTCAR, or any atomistic model. Also trigger when the user mentions POV-Ray, OVITO, Tachyon rendering, or VESTA orientation for structure visualization. Supports POV-Ray and OVITO Tachyon renderers."
---

# Structure Visualizer

Render atomic and molecular structures as high-resolution PNG images using either POV-Ray or OVITO Tachyon.

## When to use

- User asks to "render", "visualize", "draw", or "display" an atomic structure
- User mentions POSCAR, CONTCAR, .xyz, .traj, .cif files in a visualization context
- User wants publication-quality structure images
- User mentions POV-Ray, OVITO, Tachyon, or VESTA orientation

## Setup (first-time only)

Before first use, check if the required packages are installed. If not, ask the user which renderer(s) they need, then install accordingly.

### Step 1: Ask the user

Ask: "Which renderer do you need?"
- **OVITO Tachyon only** (recommended) — modern look, ambient occlusion, transparent background support
- **OVITO + POV-Ray** — adds POV-Ray for precise VESTA angle control

### Step 2: Check and install

**Check if already installed:**
```bash
conda run -n <env> python -c "import ovito; print('ovito', ovito.version_string)"
conda run -n <env> python -c "import ase; print('ase', ase.__version__)"
conda run -n <env> python -c "from PIL import Image; print('Pillow OK')"
# POV-Ray only:
conda run -n <env> which povray
conda run -n <env> python -c "import scipy; print('scipy', scipy.__version__)"
```

**Install OVITO only (recommended):**
```bash
conda run -n <env> pip install ovito ase Pillow
```

**Install OVITO + POV-Ray:**
```bash
conda run -n <env> pip install ovito ase Pillow scipy
conda run -n <env> conda install -c conda-forge povray -y
```

Replace `<env>` with the user's conda environment. On first use, ask the user which conda
environment to install into / run from, and remember their answer for subsequent runs.

### Dependencies summary

| Package | Required for | Install |
|---------|-------------|---------|
| `ovito` | OVITO Tachyon renderer (core) | `pip install ovito` |
| `ase` | Structure file I/O | `pip install ase` |
| `Pillow` | Image crop/post-processing | `pip install Pillow` |
| `scipy` | VESTA matrix -> Euler angles (POV-Ray only) | `pip install scipy` |
| `povray` | POV-Ray renderer binary (POV-Ray only) | `conda install -c conda-forge povray` |

## Environment

Always use `conda run -n <env>` for all Python execution, where `<env>` is the environment the
user chose during first-run setup. If POV-Ray was installed via conda, set the include path
with `POVRAY_INCLUDE=<env-prefix>/share/povray-3.6/include` when running `render_povray.py`
(defaults to `/usr/local/share/povray-3.6/include`).

## Renderer selection

- **OVITO Tachyon** (recommended): Ambient occlusion, transparent background (`--transparent`), modern look. Uses `scripts/render_ovito.py`.
- **POV-Ray**: Precise angle control via VESTA orientation matrix. Uses `scripts/render_povray.py`.

Default to OVITO Tachyon unless the user explicitly requests POV-Ray.

## Input formats

Read structures using ASE. Supported formats:
- POSCAR, CONTCAR (VASP)
- .xyz
- .traj (reads last frame by default: `read(path, index=-1)`)
- .cif

## Options

When the user requests a render, determine these parameters from their request (use defaults if not specified):

| Option | Description | Default |
|--------|-------------|---------|
| `renderer` | `ovito` or `povray` | `ovito` |
| `rotation` | Euler angles string like `"15z,-90x"` or VESTA matrix | `"-90x,0y,0z"` (side view) |
| `repeat` | Supercell repeat like `(2,1,1)` | `(1,1,1)` |
| `show_unit_cell` | 0=none, 1=cell, 2=cell+axes | `0` |
| `width` | Image width in pixels | `2000` |
| `height` | Image height in pixels (OVITO) | `2800` |
| `antialiasing` | Antialiasing samples, higher = smoother edges (OVITO) | `12` |
| `ao_brightness` | Ambient occlusion brightness 0-1 (OVITO) | `0.8` |
| `shadows` | Enable shadows (OVITO only) | `False` |
| `transparent` | Transparent background via native alpha channel (OVITO only) | `True` |
| `custom_colors` | Dict of element -> RGB tuple | jmol defaults |
| `index_colors` | Dict of atom index -> RGB tuple | none |
| `custom_radii` | Dict of element -> radius | renderer defaults |
| `camera_dist` | Camera distance (POV-Ray) | `50` |
| `use_custom_lighting` | Custom lighting (POV-Ray) | `False` |
| `cell_line_width` | Unit cell line width (OVITO) | `0.1` |
| `tight_crop` | Auto-crop white background (OVITO) | `False` |
| `crop_margin` | Margin in px for tight crop / transparent crop (OVITO) | `20` |

## Custom viewing angle

If the user asks how to control the viewing angle, guide them through the VESTA workflow:

1. Open the structure file in **VESTA** (free software: https://jp-minerals.org/vesta/)
2. Rotate the structure to the desired viewing angle using the mouse
3. Go to **Edit → Bonds...** or simply look at the bottom-left status bar — the current orientation matrix is shown there. Alternatively: **Edit → Vectors...** or copy from the **console output** when rotating.
4. The most reliable way: go to **Objects → Orientation...** (or press the orientation icon in the toolbar). This shows the current **3x3 rotation matrix**.
5. Copy the 9 numbers (3 rows x 3 columns) and paste them into the render command.

Example — the user pastes:
```
 0.5000 -0.8660  0.0000
 0.6124  0.3536  0.7071
-0.6124 -0.3536  0.7071
```

Pass to the render script as `--vesta-matrix "0.5 -0.866 0.0 / 0.6124 0.3536 0.7071 / -0.6124 -0.3536 0.7071"` (rows separated by `/`).

### Built-in view presets (OVITO)

For common angles without VESTA, the OVITO script supports `--view` presets:
- `front` (default), `back`, `top`, `bottom`, `left`, `right`

### VESTA matrix conversion (internal)

When a user provides a VESTA matrix, convert it to the appropriate format for the chosen renderer:

**For POV-Ray:** Convert matrix to Euler angles using scipy:
```python
from scipy.spatial.transform import Rotation as R
import numpy as np

matrix = np.array([[...], [...], [...]]) # 3x3 from VESTA
rotation = R.from_matrix(matrix)
euler = rotation.as_euler("xyz", degrees=True)
rotation_string = f"{euler[0]}x, {euler[1]}y, {euler[2]}z"
```

**For OVITO:** Convert matrix to camera direction and up vector:
```python
# VESTA matrix columns define the view axes
# Column 3 (z-axis of view) = camera direction (negated = looking toward origin)
camera_dir = -matrix[:, 2]  # negative z-axis = looking direction
camera_up = matrix[:, 1]    # y-axis = up direction
```

## Workflow

1. Read the structure file with ASE
2. Apply `wrap()` if the structure came from MD (.traj)
3. Apply `repeat()` if requested
4. Apply boundary adjustment (shift atoms near cell edge)
5. Set custom colors/radii if specified
6. Render with chosen renderer
7. Save PNG to the requested location

## Running the scripts

Both scripts accept command-line arguments. Build the command based on user options:

**OVITO (white background):**
```bash
conda run -n <env> python <skill-path>/scripts/render_ovito.py \
  --input structure.vasp \
  --output result.png \
  --view front \
  --width 2000 \
  --height 2800 \
  --show-cell 0 \
  --repeat 1 1 1 \
  --cell-line-width 0.1 \
  --no-shadows \
  --tight-crop \
  --crop-margin 50
```

**OVITO (transparent background):**
```bash
conda run -n <env> python <skill-path>/scripts/render_ovito.py \
  --input structure.vasp \
  --output result.png \
  --view front \
  --width 2000 \
  --height 2800 \
  --show-cell 0 \
  --no-shadows \
  --transparent \
  --crop-margin 50
```
When `--transparent` is used, the output PNG has a native alpha channel (no chroma key needed). Auto-crops to content bounding box with margin. Works cleanly with all element colors including white (H).

**POV-Ray:**
```bash
conda run -n <env> python <skill-path>/scripts/render_povray.py \
  --input structure.vasp \
  --output result.png \
  --rotation "-90x,0y,0z" \
  --width 2000 \
  --show-cell 0 \
  --repeat 1 1 1 \
  --camera-dist 50
```

For VESTA orientation, pass `--vesta-matrix "0.5 -0.8 0.0 / 0.6 0.3 0.7 / -0.5 -0.3 0.7"` (rows separated by `/`).

For custom colors, pass `--colors "Co:0.85,0.55,0.65 O:0.9,0.1,0.1"`.
For index colors, pass `--index-colors "0:0,1,0 5:1,0,0"`.
For custom radii, pass `--radii "Co:1.2 H:0.3"`.
