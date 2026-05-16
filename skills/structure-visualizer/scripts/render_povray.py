#!/usr/bin/env python
"""
POV-Ray renderer for atomic structures.
Part of structure-visualizer skill.
"""
import argparse
import os
import re
import numpy as np
from scipy.spatial.transform import Rotation as R
from ase.io import write, read
from ase.data.colors import jmol_colors
from PIL import Image


def parse_colors(color_str):
    """Parse color string like 'Co:0.85,0.55,0.65 O:0.9,0.1,0.1'"""
    colors = {}
    if not color_str:
        return colors
    for item in color_str.split():
        elem, rgb = item.split(":")
        colors[elem] = [float(x) for x in rgb.split(",")]
    return colors


def parse_index_colors(color_str):
    """Parse index color string like '0:0,1,0 5:1,0,0'"""
    colors = {}
    if not color_str:
        return colors
    for item in color_str.split():
        idx, rgb = item.split(":")
        colors[int(idx)] = [float(x) for x in rgb.split(",")]
    return colors


def parse_vesta_matrix(matrix_str):
    """Parse VESTA matrix string like '0.5 -0.8 0.0 / 0.6 0.3 0.7 / -0.5 -0.3 0.7'"""
    rows = matrix_str.split("/")
    matrix = np.array([[float(x) for x in row.split()] for row in rows])
    rotation = R.from_matrix(matrix)
    euler = rotation.as_euler("xyz", degrees=True)
    return f"{euler[0]}x, {euler[1]}y, {euler[2]}z"


def adjust_positions(atoms):
    """Adjust atoms near cell boundary."""
    scaled = atoms.get_scaled_positions()
    for i, pos in enumerate(scaled):
        for j in range(2):
            if scaled[i][j] < 0.05:
                scaled[i][j] += 1
    atoms.set_scaled_positions(scaled)


def remove_specular(pov_file):
    """Remove specular highlights from POV file."""
    with open(pov_file, "r") as f:
        content = f.read()
    content = re.sub(
        r"finish\s*{[^}]+}",
        lambda m: re.sub(r"specular\s+[\d.]+", "specular 0.0",
                         re.sub(r"phong\s+[\d.]+", "phong 0.0", m.group(0))),
        content,
    )
    with open(pov_file, "w") as f:
        f.write(content)


def add_custom_lighting(pov_file, intensity=1.0, ambient=0.2):
    """Add custom lighting to POV file."""
    with open(pov_file, "r") as f:
        content = f.read()
    lighting = f"""
global_settings {{ ambient_light rgb <{ambient}, {ambient}, {ambient}> }}
light_source {{ <10, 20, -10> color rgb <{intensity}, {intensity}, {intensity}>
    area_light <2, 0, 0>, <0, 2, 0>, 3, 3 adaptive 1 jitter }}
light_source {{ <-10, 10, 10> color rgb <{intensity*0.6}, {intensity*0.6}, {intensity*0.7}> }}
background {{ color rgb <1, 1, 1> }}
"""
    pos = content.find("camera {")
    if pos != -1:
        content = content[:pos] + lighting + content[pos:]
    else:
        content = lighting + content
    with open(pov_file, "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="POV-Ray structure renderer")
    parser.add_argument("--input", "-i", required=True, help="Input structure file")
    parser.add_argument("--output", "-o", required=True, help="Output PNG path")
    parser.add_argument("--rotation", "-r", default="-90x,0y,0z", help="Rotation string")
    parser.add_argument("--vesta-matrix", default=None, help="VESTA orientation matrix (rows separated by /)")
    parser.add_argument("--width", "-w", type=int, default=2000, help="Image width")
    parser.add_argument("--camera-dist", type=float, default=50, help="Camera distance")
    parser.add_argument("--show-cell", type=int, default=0, choices=[0, 1, 2], help="Show unit cell")
    parser.add_argument("--repeat", nargs=3, type=int, default=[1, 1, 1], help="Supercell repeat")
    parser.add_argument("--colors", default=None, help="Custom colors: 'Co:0.85,0.55,0.65 O:0.9,0.1,0.1'")
    parser.add_argument("--index-colors", default=None, help="Index colors: '0:0,1,0 5:1,0,0'")
    parser.add_argument("--custom-lighting", action="store_true", help="Use custom lighting")
    parser.add_argument("--light-intensity", type=float, default=1.0)
    parser.add_argument("--ambient-light", type=float, default=0.2)
    parser.add_argument("--frame", type=int, default=-1, help="Frame index for trajectory files")
    args = parser.parse_args()

    # Handle VESTA matrix
    rotation = args.rotation
    if args.vesta_matrix:
        rotation = parse_vesta_matrix(args.vesta_matrix)
        print(f"VESTA matrix -> rotation: {rotation}")

    # Read structure
    if args.input.endswith(".traj"):
        atoms = read(args.input, index=args.frame)
        atoms.wrap()
    else:
        atoms = read(args.input)

    # Repeat
    rep = tuple(args.repeat)
    if rep != (1, 1, 1):
        atoms = atoms.repeat(rep)

    # Adjust boundary atoms
    adjust_positions(atoms)

    # Build color list
    custom = parse_colors(args.colors)
    idx_colors = parse_index_colors(args.index_colors)
    colors = []
    for i, atom in enumerate(atoms):
        if i in idx_colors:
            colors.append(idx_colors[i])
        elif atom.symbol in custom:
            colors.append(custom[atom.symbol])
        else:
            colors.append(jmol_colors[atom.number].tolist())

    # Write POV file
    renderer = write(
        "./temp.pov",
        atoms,
        rotation=rotation,
        show_unit_cell=args.show_cell,
        colors=colors,
        povray_settings={
            "canvas_width": args.width,
            "camera_dist": args.camera_dist,
            "camera_type": "orthographic",
        },
    )

    # Post-process
    if args.custom_lighting:
        add_custom_lighting("./temp.pov", args.light_intensity, args.ambient_light)
    remove_specular("./temp.pov")

    # Add POV-Ray library path
    with open("temp.ini", "a") as f:
        f.write('\nLibrary_Path="/home/jumoon/povray-3.6/include"\n')

    # Render
    renderer.render()

    # Save
    img = Image.open("./temp.png")
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    img.save(args.output)
    print(f"Saved: {args.output}")

    # Cleanup
    for f in ["./temp.ini", "./temp.pov", "./temp.png"]:
        if os.path.isfile(f):
            os.remove(f)


if __name__ == "__main__":
    main()
