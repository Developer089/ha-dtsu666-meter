# Branding / integration icon

Home Assistant and HACS **do not read icons from this repository**. The icon
shown for an integration comes from the central
[`home-assistant/brands`](https://github.com/home-assistant/brands) repo. Until
a brand is accepted there, HA shows a generic placeholder — that is expected.

`dtsu666_meter.svg` here is an **original placeholder mark** (a neutral
energy-meter motif), used only for this repo's README / GitHub social preview.
It is intentionally **not** the CHINT corporate logo.

## How to get a real icon into Home Assistant

Submit a pull request to `home-assistant/brands`:

```
brands/
  custom_integrations/
    dtsu666_meter/
      icon.png      # 256 x 256, square, transparent background, trimmed
      logo.png      # optional, wider wordmark; transparent background
      icon@2x.png   # optional 512 x 512 hDPI
```

Requirements (see `home-assistant/brands` CONTRIBUTING):

- PNG, transparent background, content trimmed to the edges.
- `icon.png` exactly 256×256 (square). `icon@2x.png` 512×512 if provided.
- Optimised (e.g. `pngquant` / `oxipng`).
- The domain folder name **must** match the integration domain:
  `dtsu666_meter`.

Steps:

1. Fork `home-assistant/brands`, add the files above.
2. `python3 -m script.hassfest` style checks run in CI there — keep sizes exact.
3. Open the PR; the HA team reviews. Once merged, HA/HACS pick the icon up
   automatically (no release needed on this side).

## About the CHINT logo (trademark)

The CHINT logo is CHINT's trademark. `home-assistant/brands` does accept
manufacturer logos for device integrations (common practice), **but the image
must be an officially sourced asset** — obtain it from CHINT brand resources or
an authorised source. Do not trace/recreate it.

This project cannot generate or reproduce that trademarked raster logo. Drop an
officially sourced `icon.png` (256×256, transparent) into this folder and it can
be wired into the brands PR.
