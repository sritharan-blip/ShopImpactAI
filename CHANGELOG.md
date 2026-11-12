# Changes

## Liquid glass edition

- Rebuilt the visual system around frosted glass, aurora light, luminous edges, a dimensional orb, and floating cards driven by session data.
- Applied appearance tokens before rendering controls and removed foreground/background color transitions to prevent unreadable text while switching.
- Added a global quick-actions deck and Decision lab for cost per use, budget fit, and wishlist pause plans.
- Rebuilt the README with a new animated cover, guided setup, feature overview, data boundaries, and architecture reference.
- Extended regression and real-Chrome coverage to the new feature and repeated theme changes.

## 2026-11-12

- Introduced Daylight and Midnight appearances with coordinated surfaces, inputs, tables, charts, and illustration colors.
- Added an animated dashboard hero, orbital decoration, inspiration strip, product illustrations, milestone cards, hover feedback, and page transitions.
- Added Reduce motion and retained High contrast; operating-system motion preferences are respected.
- Added a self-hosted animated README banner and a reproducible Pillow generation script.
- Replaced static recommendation ordering with an explainable local TF-IDF content model plus category, budget, and reduction ranking signals.
- Split the single-file app into focused modules.
- Renamed carbon reductions to carbon_saved_kg and corrected reward descriptions and goals.
- Corrected manually logged greener scenarios to reduce the recorded footprint as well as calculate the reduction.
- Introduced version 2 backups preserving footprint and baseline snapshots, identifiers, and wishlist dates; retained legacy import support.
- Made malformed backup restoration atomic and bounded CSV parsing by bytes and rows; reject duplicate headers and invalid values.
- Fixed Python 3.10 f-string compatibility in checkout, literal purchase searches, unsupported Streamlit arguments, and swap quantity previews.
- Added domain regression tests, Streamlit interaction tests, and a Python-version CI matrix.
