# Pigment and preservation

The built-in image tool generated one transparent motif: a shallow broken
U-shaped ochre nest holding three irregular pebble dots, two charcoal and one
chalk. The prompt requested rough, uneven, worn cave pigment; only earth
colours; no writing, signatures, borders, hands, people or animals. The image
tool returned a 1536 × 1024 RGBA PNG. No alternative image was saved.

Imported it directly to the required final artifact path, then replaced that
transient draft with the complete wall using `finish_wall41.py`. The compositor
samples the motif's tight bounding region, discards transparent/non-pigment
pixels and blends only those pixels into unused left-hand rock. The source
wall-v20 hash is checked before compositing. The evidence file records both
hashes, final dimensions, region and pixel comparison. The output is the
original 1254 × 1254 RGB wall plus that one mark, not a regenerated cave.

Only final wall-v21 and its required 512 × 512 JPEG were saved as new images
in the workspace. The JPEG was produced with ffmpeg scale=512:512, quality 7.
Both were viewed and structurally inspected. No hands or handprints were added;
Pepe's folded limbs expose no fingers. No writing or prohibited symbol was
observed. The added pigment is darker/smaller at preview scale; no other unmet
visual requirement was observed.
