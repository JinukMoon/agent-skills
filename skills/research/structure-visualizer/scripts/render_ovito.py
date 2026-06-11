#!/usr/bin/env python
"""
OVITO Tachyon renderer for atomic structures.
Part of structure-visualizer skill.
"""
import argparse
import os
import numpy as np
from ovito.io import import_file
from ovito.vis import TachyonRenderer, Viewport, ParticlesVis
from ase.io import read, write as ase_write
from PIL import Image, ImageOps


def parse_colors(color_str):
    """Parse color string like 'Co:0.85,0.55,0.65 O:0.9,0.1,0.1'"""
    colors = {}
    if not color_str:
        return colors
    for item in color_str.split():
        elem, rgb = item.split(":")
        colors[elem] = tuple(float(x) for x in rgb.split(","))
    return colors


def parse_radii(radii_str):
    """Parse radii string like 'Co:1.2 H:0.3'"""
    radii = {}
    if not radii_str:
        return radii
    for item in radii_str.split():
        elem, r = item.split(":")
        radii[elem] = float(r)
    return radii


def parse_vesta_matrix(matrix_str):
    """Parse VESTA orientation matrix, return camera_dir and camera_up.
    VESTA matrix rows define the view coordinate system:
      row 0 = right, row 1 = up, row 2 = viewing direction (into screen).
    OVITO camera_dir points from camera toward the scene (opposite of VESTA row 2).
    """
    rows = matrix_str.split("/")
    matrix = np.array([[float(x) for x in row.split()] for row in rows])
    camera_dir = tuple(-matrix[2])   # negative of row 2 (view direction)
    camera_up = tuple(matrix[1])     # row 1 = up
    return camera_dir, camera_up


VIEW_MAP = {
    "front": Viewport.Type.Front,
    "top": Viewport.Type.Top,
    "back": Viewport.Type.Back,
    "right": Viewport.Type.Right,
    "left": Viewport.Type.Left,
    "bottom": Viewport.Type.Bottom,
}


def main():
    parser = argparse.ArgumentParser(description="OVITO Tachyon structure renderer")
    parser.add_argument("--input", "-i", required=True, help="Input structure file")
    parser.add_argument("--output", "-o", required=True, help="Output PNG path")
    parser.add_argument("--view", default="front", help="Preset view: front/top/back/right/left/bottom")
    parser.add_argument("--vesta-matrix", default=None, help="VESTA orientation matrix (rows separated by /)")
    parser.add_argument("--width", "-w", type=int, default=2000, help="Image width")
    parser.add_argument("--height", type=int, default=2800, help="Image height")
    parser.add_argument("--show-cell", type=int, default=0, choices=[0, 1, 2], help="Show unit cell")
    parser.add_argument("--cell-line-width", type=float, default=0.1, help="Cell line width")
    parser.add_argument("--repeat", nargs=3, type=int, default=[1, 1, 1], help="Supercell repeat")
    parser.add_argument("--colors", default=None, help="Custom colors: 'Co:0.85,0.55,0.65'")
    parser.add_argument("--radii", default=None, help="Custom radii: 'Co:1.2 H:0.3'")
    parser.add_argument("--no-shadows", action="store_true", help="Disable shadows")
    parser.add_argument("--ao-brightness", type=float, default=0.8, help="Ambient occlusion brightness")
    parser.add_argument("--antialiasing", type=int, default=12, help="Antialiasing samples")
    parser.add_argument("--frame", type=int, default=-1, help="Frame index for trajectory")
    parser.add_argument("--transparent", action="store_true", help="Transparent background (alpha channel)")
    parser.add_argument("--tight-crop", action="store_true", help="Auto-crop white background")
    parser.add_argument("--crop-margin", type=int, default=20, help="Margin in px for tight crop")
    parser.add_argument("--fixed-fov", type=float, default=None, help="Fixed FOV (orthographic width) for uniform zoom across renders")
    parser.add_argument("--print-fov", action="store_true", help="Print auto-calculated FOV and exit without rendering")
    args = parser.parse_args()

    # Read with ASE, process, save temp xyz
    if args.input.endswith(".traj"):
        atoms = read(args.input, index=args.frame)
        atoms.wrap()
    else:
        atoms = read(args.input)

    rep = tuple(args.repeat)
    if rep != (1, 1, 1):
        atoms = atoms.repeat(rep)

    # Adjust boundary atoms (wrap=False to preserve positions)
    scaled = atoms.get_scaled_positions(wrap=False)
    for i in range(len(scaled)):
        for j in range(2):
            if scaled[i][j] < 0.05:
                scaled[i][j] += 1
    atoms.set_scaled_positions(scaled)

    tmp = "/tmp/_ovito_temp.xyz"
    ase_write(tmp, atoms)

    # Import into OVITO
    pipeline = import_file(tmp)
    data = pipeline.compute()

    # Set colors and radii
    custom_colors = parse_colors(args.colors)
    custom_radii = parse_radii(args.radii)
    types_prop = pipeline.source.data.particles_.particle_types_
    for name in set(atoms.get_chemical_symbols()):
        try:
            ptype = types_prop.type_by_name_(name)
            if name in custom_colors:
                ptype.color = custom_colors[name]
            if name in custom_radii:
                ptype.radius = custom_radii[name]
        except KeyError:
            pass

    # Particles visual
    particles_vis = pipeline.source.data.particles.vis
    particles_vis.shape = ParticlesVis.Shape.Sphere

    # Cell visual
    cell_vis = pipeline.source.data.cell_.vis
    cell_vis.enabled = args.show_cell > 0
    cell_vis.line_width = args.cell_line_width
    cell_vis.rendering_color = (0.0, 0.0, 0.0)

    # Add to scene
    pipeline.add_to_scene()

    # Viewport
    if args.vesta_matrix:
        camera_dir, camera_up = parse_vesta_matrix(args.vesta_matrix)
        vp = Viewport()
        vp.camera_dir = camera_dir
        vp.camera_up = camera_up
        vp.zoom_all(size=(args.width, args.height))
    else:
        vp_type = VIEW_MAP.get(args.view, Viewport.Type.Front)
        vp = Viewport(type=vp_type)
        vp.zoom_all(size=(args.width, args.height))

    if args.print_fov:
        print(f"FOV: {vp.fov}")
        pipeline.remove_from_scene()
        os.remove(tmp)
        return

    if args.fixed_fov is not None:
        vp.fov = args.fixed_fov

    # Tachyon renderer
    renderer = TachyonRenderer()
    renderer.ambient_occlusion = True
    renderer.ambient_occlusion_brightness = args.ao_brightness
    renderer.antialiasing_samples = args.antialiasing
    renderer.direct_light_intensity = 0.9
    renderer.shadows = not args.no_shadows

    # Render
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    render_kwargs = dict(
        filename=args.output,
        size=(args.width, args.height),
        renderer=renderer,
    )
    if args.transparent:
        render_kwargs["alpha"] = True
    else:
        render_kwargs["background"] = (1.0, 1.0, 1.0)
    vp.render_image(**render_kwargs)

    if args.tight_crop or args.transparent:
        img = Image.open(args.output)
        if args.transparent:
            bbox = img.split()[-1].getbbox()
        else:
            diff = ImageOps.invert(img.convert("RGB"))
            bbox = diff.getbbox()
        if bbox:
            m = args.crop_margin
            crop_box = (max(0, bbox[0]-m), max(0, bbox[1]-m),
                        min(img.width, bbox[2]+m), min(img.height, bbox[3]+m))
            img = img.crop(crop_box)
            img.save(args.output)

    print(f"Saved: {args.output}")

    # Cleanup
    pipeline.remove_from_scene()
    os.remove(tmp)


if __name__ == "__main__":
    main()
