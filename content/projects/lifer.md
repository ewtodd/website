---
title: "lifer"
description: "A bird photo rematch pipeline: BioCLIP candidates against a taxonomy, reviewed in darktable, published as a life list."
summary: "Turns my own photographs into a life list: embed each photo with BioCLIP, shortlist candidate species, review in darktable, and publish the confirmed sightings."
weight: 50
status: "Active"
role: "Author"
license: "MIT"
stack: ["Python", "Nix", "BioCLIP", "darktable", "Flask"]
repo: "https://github.com/ewtodd/lifer"
lastmod: 2026-10-18
---
<!---->
The pipeline behind the [public life list](/birds/). A photo becomes a published
sighting only after it has passed through a shortlist and a human review.
<!---->
## How a photo becomes a sighting
<!---->
**Embed.** Every photo is embedded with a BioCLIP model, which projects it into
the same space as the shared taxonomic list. The nearest matches are the
candidate species for that photo.
<!---->
**Review.** Candidates are shown in a darktable review workflow. The certain ones
are confirmed straight away; the uncertain ones stay on the shortlist until
they can be checked.
<!---->
**Grade.** Each confirmed sighting carries a reliability grade, so the life list
is honest about what was a positive identification and what was not.
<!---->
**Record.** A confirmed outing becomes a sighting in a JSON registry, and
recording it opens a pull request that reuses the photo rather than re-importing
it. The photo is stored once and referenced from the list.
<!---->
The published list, in taxonomic order with the first and latest sighting for
each species and the photos that back them, is at [the birds page](/birds/).
