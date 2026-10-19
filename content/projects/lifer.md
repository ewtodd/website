---
title: "lifer"
description: "Finds the birds in my raw photos, suggests species with BioCLIP against the local species list, and keeps my life list current."
summary: "Turns a card full of raw bird photos into reviewed sightings and an up-to-date life list, with first-pass edits for the keepers."
weight: 50
status: "Active"
role: "Author"
license: "MIT"
stack: ["Python", "Nix", "BioCLIP", "darktable", "Flask"]
repo: "https://github.com/ewtodd/lifer"
lastmod: 2026-10-18
---
<!---->
The pipeline behind the [public life list](/birds/). A trip's raw photos go in;
what comes out is a short list of sightings for me to check, and a life list
that stays current without spreadsheet work.
<!---->
## How a trip becomes sightings
<!---->
**Find.** A detector locates each bird in the camera's embedded preview, crops
it, and groups bursts of frames into single encounters.
<!---->
**Identify.** BioCLIP 2.5 ranks candidate species for each encounter against
the species recorded on iNaturalist for that county, weighted gently by how
common each is that time of year. Species that are rare for the place and
season are flagged rather than suppressed.
<!---->
**Review.** A small web app groups encounters by species. I confirm or correct
each group, fix a crop when the detector picked a branch, and choose the best
frame. Nothing reaches the list without that review.
<!---->
**Edit.** For the keepers, lifer writes a first-pass darktable edit in my usual
style; I finish the photos that need local work in darktable.
<!---->
The published list, in taxonomic order with the first and latest sighting for
each species and the photos behind them, is on [the birds page](/birds/).
