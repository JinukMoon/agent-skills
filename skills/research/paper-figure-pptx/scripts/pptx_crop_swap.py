"""Replace fig2pptx panel pictures with the FULL-resolution source images cropped inside PowerPoint.

Why: cropping pixels in matplotlib (imshow of a slice) throws away resolution and bakes the crop in.
A PowerPoint crop (`<a:srcRect>`) keeps every pixel of the original render and the user can re-crop
by dragging the crop handles. Use this for structure renders (OVITO/POV-Ray) that show only a region.

Usage (after `export_figure(fig, pptx)`; the figure's axes must have been created in the same order
as `sources`, or pass `order='grid'` to map pictures row-major by their slide position):

    from pptx_crop_swap import swap_pictures_with_crop
    swap_pictures_with_crop(pptx_path, sources, crop=0.28)           # centred square, 28 % of min(w,h)
    swap_pictures_with_crop(pptx_path, sources, crop=(l, r, t, b))   # explicit fractions per side
    swap_pictures_with_crop(pptx_path, sources, crop=[...per picture...])

`sources` = list of image paths, one per picture in the slide, row-major (top row left->right, then next
row). Use None for a picture that should be left untouched (a plotted panel rather than a render).
Orphaned image parts left by the removed pictures are dropped so the file does not bloat.
"""
import os
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from PIL import Image
from fig2pptx import save_pptx


def _crop_fracs(src, crop):
    if isinstance(crop, (tuple, list)) and len(crop) == 4:
        return tuple(float(c) for c in crop)
    w, h = Image.open(src).size; side = int(min(w, h) * float(crop))
    lr = (w - side) / (2 * w); tb = (h - side) / (2 * h)
    return lr, lr, tb, tb


def swap_pictures_with_crop(pptx_path, sources, crop=0.3, outline_pt=0.75, slide_index=0, order='grid'):
    prs = Presentation(pptx_path); slide = prs.slides[slide_index]
    pics = [sh for sh in slide.shapes if sh.shape_type == 13]
    if len(pics) != len(sources):
        raise ValueError(f'{len(pics)} pictures in the slide but {len(sources)} sources given')
    if order == 'grid':   # row-major by slide position
        ys = sorted({round(sh.top + sh.height / 2, -4) for sh in pics})
        pics = sorted(pics, key=lambda sh: (min(range(len(ys)), key=lambda i: abs(ys[i] - (sh.top + sh.height / 2))), sh.left))
    crops = crop if isinstance(crop, list) else [crop] * len(pics)
    for sh, src, cr in zip(pics, sources, crops):
        if src is None: continue          # keep this picture as fig2pptx made it (e.g. a plotted panel)
        l, r, t, b = _crop_fracs(src, cr)
        new = slide.shapes.add_picture(src, sh.left, sh.top, sh.width, sh.height)
        new.crop_left, new.crop_right, new.crop_top, new.crop_bottom = l, r, t, b
        new.name = 'panel_' + os.path.basename(src)
        if outline_pt:
            new.line.color.rgb = RGBColor(0, 0, 0); new.line.width = Pt(outline_pt)
        sh._element.getparent().remove(sh._element)
    # drop image parts that no shape references any more (python-pptx keeps them otherwise -> huge file)
    used = set()
    for sh in slide.shapes:
        for el in sh._element.iter():
            for k, v in el.attrib.items():
                if k.endswith('}embed') or k.endswith('}link'): used.add(v)
    for rId, rel in list(slide.part.rels.items()):
        if rel.reltype.endswith('/image') and rId not in used: slide.part.drop_rel(rId)
    written = save_pptx(prs, pptx_path)   # -> <name>_v2.pptx if the deck is open in PowerPoint
    if written != pptx_path:
        print(f"    !! run pptx2figs.py on {written}, not on the locked original")
    return len(pics)
