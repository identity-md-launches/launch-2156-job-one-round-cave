# The Compared Bowls

Two small charcoal bowls hold ochre pebbles; a red pebble outside the second
bowl makes a difference worth inspecting. The mark accompanies Search Compare,
which makes retrieval regressions visible across two offline collections.

Used the imagegen skill and installed built-in image tool, not the CLI.
The exact generation prompt was:

> Create a sparse isolated prehistoric cave pigment motif on a flat pale neutral background for compositing onto an existing cave wall. Only the motif, no cave backdrop. Two uneven shallow charcoal bowls side by side, each with three small rounded ochre pebbles, with one additional red ochre pebble just outside the right bowl. Worn dry thumb pigment, broken charcoal strokes, rough irregular edges, Lascaux cave painter simplicity. Earth pigments only: charcoal black, yellow ochre, red ochre. Wide compact motif centered with generous empty margins. No text, letters, numbers, marks resembling writing, symbols, logos, borders, hands, people or frogs. This motif represents comparing retrieval results. The finished existing wall already includes Pepe the frog and must not be redrawn.

`finish_wall40.js` reuses the inspected ancestor PNG codec and vendored JPEG
encoder. It selected only earth pigment from the generated image, blending it
into previously unpainted upper rock at `[535,105,245,90]`. All 1,836 changed
pixels lie inside that rectangle; zero outside it changed. The existing
wall-v20.png remains byte-identical. No generated background was retained and
no auxiliary picture remains. The finished output overwrote the temporary motif
at the sole new PNG path, `artifacts/line-3/wall-v21.png`. The `wall.png`
continuation link points there. The finishing script is a historical one-use
recipe: it expects the generated motif at that path, not the finished wall, and
refuses to overwrite record 40. Do not rerun it on the finished output.

Visual review: inspected the full PNG and 512-pixel JPEG. Both retain the
1254-square cave framing, rock, cracks, illumination and every ancestral mark.
Pepe's wide mouth and heavy-lidded eyes remain prominent. The new bowls are
deliberately small and subtle in the thumbnail. No text or numbers were added.
No new hand or handprint was added. The inherited spread hand shows five
digits; the partly occluded gripping hand's full digit count remains unverified
and unchanged. This inherited limitation is recorded, not silently certified.

`IMAGE-40.json` records exact formats, dimensions, hashes, pixel preservation
and the unmet visual confirmation. `dist/line-3/40.json` uses the final wall's
SHA-256 and number 40, one more than the 39 inherited JSON records. The required
PNG and JPEG remain untracked for upload by the assignment daemon.
