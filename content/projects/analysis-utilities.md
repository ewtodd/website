---
title: "Analysis-Utilities"
description: "C++/ROOT toolkit for nuclear measurement data — binary readers, waveform processing, and GPU-accelerated photopeak fitting."
weight: 10
---

C++ utilities for analysis of nuclear measurement data, built on
[ROOT](https://root.cern/), with a focus on ergonomics and performance. It reads
CAEN digitizer output via CoMPASS and WaveDump, and SOL-format data from the
SOLARIS DAQ, then takes it through waveform processing and into photopeak fits.

> **[Full documentation and API reference → au.ethanwtodd.com](https://au.ethanwtodd.com)**

## What it does

**Binary readers.** CoMPASS `.bin`, WaveDump DT5742, and SOLARIS `.sol`,
including trace-carrying block formats and time-bounded run splitting that runs
close to disk speed.

**Waveform processing.** Baseline subtraction, fraction-of-peak trigger finding,
cropping, and feature extraction (pulse height, short/long integrals, PSD
ratio), with quality cuts and parallel multi-file processing.

**Photopeak fitting.** Two backends with identical APIs — a `TF1` binned
chi-squared fit, and an unbinned extended maximum-likelihood RooFit fit built
from custom `RooAbsPdf` components for the step and tail structure seen in
segmented semiconductor detectors. Components are selected by a
group-and-prune search rather than being fixed up front.

**GPU acceleration.** Each custom PDF ships a CUDA kernel. When RooFit hands
`doEval` device-resident buffers it launches the kernel instead of the host
loop, taking a 4 M-event unbinned likelihood fit from roughly two minutes on an
OpenMP-batched CPU path to about six seconds.

| Path | Single fit | Simultaneous fit |
|------|-----------:|-----------------:|
| Scalar `evaluate()` (legacy) | ~minutes | ~minutes |
| OpenMP batched `doEval` | ~2 min | ~3 min |
| CUDA kernels | ~6 s | ~36 s |

**Interactive fitting.** A ROOT GUI editor for adjusting a fit by hand when the
automated pass needs help, with a live residual panel; accepted parameters are
persisted and reloaded so the manual step happens once.

**Python bridge.** The whole C++ API is reachable from PyROOT, alongside a
loader that pulls ROOT TTrees into numpy arrays and pandas DataFrames with
on-disk caching, for downstream machine learning work.

## How it is built

Nix flake, CMake, and ROOT 6.38+. The flake exposes CPU and CUDA library
variants plus a Python package, and downstream projects start from a template
with `nix flake init`. A binary cache serves the expensive CUDA-overlaid ROOT
build so collaborators do not have to compile it.

[Source on GitHub](https://github.com/ewtodd/Analysis-Utilities)
