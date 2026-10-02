---
title: "Analysis-Utilities"
description: "C++/ROOT toolkit for nuclear measurement data — binary readers, waveform processing, and GPU-accelerated photopeak fitting."
summary: "The C++/ROOT library the rest of the analysis is written against: digitizer readers, waveform processing, and photopeak fits that run on the GPU."
weight: 10
status: "Active"
role: "Author"
license: "MIT"
stack: ["C++", "ROOT", "CUDA", "RooFit", "Nix", "CMake"]
repo: "https://github.com/ewtodd/Analysis-Utilities"
docs: "https://docs.ethanwtodd.com/analysis-utilities/"
docsKind: "API reference"
---
<!---->
C++ utilities for analysis of nuclear measurement data, built on
[ROOT](https://root.cern/), with a focus on ergonomics and performance.
It reads
CAEN digitizer output via CoMPASS and WaveDump, and SOL-format data from the
[SOLARIS DAQ](https://github.com/goluckyryan/SOLARIS_DAQ), then takes it through
waveform processing and into photopeak fits.
<!---->
Everything downstream of it — the MUSIC analysis, the machine-learning work on
scintillator pulse shapes — starts from this library rather than from a fresh
pile of macros.
<!---->
## What it does
<!---->
**Binary readers.** CoMPASS `.bin`, WaveDump DT5742, and SOLARIS `.sol`,
including trace-carrying block formats and time-bounded run splitting that runs
close to disk speed.
<!---->
**Waveform processing.** Baseline subtraction, fraction-of-peak trigger finding,
cropping, and feature extraction (pulse height, short and long integrals, PSD
ratio), with quality cuts and parallel multi-file processing.
<!---->
**Photopeak fitting.** Two backends with identical APIs — a `TF1` binned
chi-squared fit, and an unbinned extended maximum-likelihood RooFit fit built
from custom `RooAbsPdf` components for the step and tail structure seen in
segmented semiconductor detectors.
Components are selected by a
group-and-prune search rather than being fixed up front.
<!---->
**Interactive fitting.** A ROOT GUI editor for adjusting a fit by hand when the
automated pass needs help, with a live residual panel.
Accepted parameters are
persisted and reloaded, so the manual step happens once.
<!---->
**Python bridge.** The whole C++ API is reachable from PyROOT, alongside a
loader that pulls ROOT TTrees into NumPy arrays and pandas DataFrames with
on-disk caching, for downstream machine learning work.
<!---->
## GPU acceleration
<!---->
Each custom PDF ships a CUDA kernel.
When RooFit hands `doEval` device-resident
buffers, the PDF launches the kernel instead of running the host loop.
The
practical effect is that an unbinned likelihood fit over four million events
stops being something you start and walk away from.
<!---->
| Path | Single fit | Simultaneous fit |
|------|-----------:|-----------------:|
| Scalar `evaluate()` (legacy) | ~minutes | ~minutes |
| OpenMP batched `doEval` | ~2 min | ~3 min |
| CUDA kernels | ~6 s | ~36 s |
<!---->
## How it is built
<!---->
Nix flake, CMake, and ROOT 6.38+.
The flake exposes CPU and CUDA library
variants plus a Python package, and downstream projects start from a template.
A binary cache serves the expensive CUDA-overlaid ROOT build, so collaborators
do not have to compile it.
<!---->
{{< terminal title="e-work@e-desktop — new project" >}}
$ nix flake init -t github:ewtodd/Analysis-Utilities --refresh
$ nix develop
# ROOT, the compiled libraries and the include paths, pinned
ROOT 6.40 · CUDA 13 · analysis-utilities ready

$ root -l macro.cpp+
{{< /terminal >}}
<!---->
The Python template is a second entry point, adding the Python package and the
machine-learning libraries on top of the same pinned ROOT.
