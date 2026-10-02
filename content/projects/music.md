---
title: "MUSIC"
description: "Analysis for the MUSIC active-target ionization chamber at Argonne — event building, beam calibration, and cross-section extraction."
summary: "Monorepo for the active-target ionization chamber at Argonne: one shared analysis tree, compiled separately against each experiment's configuration."
weight: 20
status: "Active"
role: "Author"
license: "MIT"
stack: ["C++", "ROOT", "CUDA", "TOML", "Nix", "Python"]
repo: "https://github.com/ewtodd/MUSIC"
docs: "https://docs.ethanwtodd.com/music/"
docsKind: "API reference"
---
<!---->
Analysis code for data from the Multi-Sampling Ionization Chamber at the ATLAS
accelerator facility, Argonne National Laboratory.
MUSIC is an active target:
the gas it is filled with is both the target and the detector, so a single run
records the full excitation function of a reaction rather than one point of it.
<!---->
I use it to measure the <sup>37</sup>Cl(α, n)<sup>40</sup>K cross section.
<!---->
## A monorepo, not a fork per experiment
<!---->
Every experiment that runs on MUSIC wants the same event building and a
different set of constants.
Forking the analysis per experiment is how that
usually goes, and it is how the two copies then drift apart.
<!---->
Instead there is one shared tooling tree, compiled separately against each
experiment's configuration.
Each dataset — `37Cl`, `87Rb` — lives under
`analysis/<dataset>/` and supplies only its own `Constants.cpp` and control
TOMLs.
A fix to event building is a fix everywhere, immediately.
<!---->
{{< terminal title="e-work@e-desktop — music" >}}
$ nix build
# builds music-tooling-37Cl, the default package
$ nix build .#87Rb
$ nix develop .#37Cl
$ ./result/bin/pipeline
four digitizers merged · 1.2e9 hits sorted on GPU
<!---->
{{< /terminal >}}
<!---->
## What the analysis can do
**Offline correction for mismatched trapezoidal filter settings.** The preamps MUSIC uses can be less than reliable, so they are often swapped during experiments.
This can lead to pole zero settings that do not match preamp decay times, which leads to measured pulse heights being systematically wrong.
This analysis uses the known trapezoidal filter properties as well as unique properties of beam signatures in MUSIC to correct for this!
<!---->
**Offline time synchronisation.** Historic MUSIC experiments had four digitizers free-running, so
there is no hardware trigger tying them together.
The beam can play this role; its time
structure is a known periodic signature present in all four streams, and fitting
that structure recovers the offsets after the fact.
<!---->
**GPU timestamp sorting.** Merging four unsynchronised streams means sorting on
the order of a billion timestamps per run.
That sort is a CUDA kernel, `dlopen`d
at runtime so the same binary still runs on a machine without a GPU, falling
back to the CPU path.
<!---->
**Event building and calibration.** Anode-by-anode energy calibration, beam
identification, and the tagging that separates reaction events from the beam
that produced them.
<!---->
**Cross-section extraction.** Excitation functions from the tagged events, with
the per-anode energy loss handled where it belongs rather than in a spreadsheet.
<!---->
## Built on
<!---->
The flake pins ROOT with CUDA, a C++ toolchain, `tomlplusplus`, and
[Analysis-Utilities]({{< relref "analysis-utilities" >}}) as a library input, so
the two projects are always compiled against each other at a known revision.
The documentation build fails on any Doxygen warning, which is what keeps the
published reference honest.
