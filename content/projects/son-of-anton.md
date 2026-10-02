---
title: "son-of-anton"
description: "An always-on agent harness with a separate physics research loop, reachable from a terminal or from Signal."
summary: "An always-on agent you can talk to from a terminal or from Signal, with a separate research loop that runs generated code against real detector data in a sandbox."
weight: 30
status: "Active"
role: "Author, hard fork"
license: "MIT"
stack: ["Python", "Textual", "Nix", "uv2nix", "vLLM"]
host: "e-desktop, against local models on son-of-anton"
repo: "https://github.com/ewtodd/son-of-anton"
---
<!---->
An always-on agent with two modes: a normal agent loop, and a physics research
loop.
It is a hard fork of [Nous Research's
hermes-agent](https://github.com/NousResearch/hermes-agent), stripped down to a
smaller daemon, keeping that project's learning loop — skills, memory, session
search, cron — and replacing the archived `temple` harness I ran before it.
<!---->
It talks over Discord, Slack and Signal, and the terminal interface is a Textual
application modelled on [opencode](https://github.com/sst/opencode).
<!---->
## The physics mode is explicit
<!---->
A message never starts a research run by itself.
There is no keyword routing:
you ask for a problem to be created for a dataset, or you run
`son-of-anton problem run`, and nothing else triggers it.
<!---->
When it does run, the Autophysicist is a research manager with append-only
memory, a windowed scratchpad, a token budget and a `submit_final_answer` tool.
It dispatches ephemeral sub-agents that execute code, in a git-versioned scratch
directory, with every iteration reviewed by a critic from outside the loop.
<!---->
## Where generated code actually runs
<!---->
Not in the agent's own interpreter. That environment deliberately ships no
scientific stack, because most sessions never run a physics turn and the
dependency scope rule is "only packages every session uses".
<!---->
Instead computations run under a separate interpreter inside a bubblewrap
sandbox, with the lab's data mounted read-only:
<!---->
{{< terminal title="ewtodd@e-desktop — son-of-anton" >}}
$ nix build .#physics-runtime
# ROOT, analysis_utilities, numpy, scipy, sympy,
# matplotlib, pandas, scikit-learn, xgboost, h5py
$ export SON_OF_ANTON_PHYSICS_PYTHON=./result/bin/python3
$ son-of-anton problem run 37Cl-clustering
sandbox: /data mounted read-only · critic enabled
<!---->
{{< /terminal >}}
<!---->
That runtime is built from the
[Analysis-Utilities]({{< relref "analysis-utilities" >}}) flake input rather than
from this project's nixpkgs, because its Python package has to be paired with
the interpreter it was compiled against.
<!---->
## Why it diverged from its ancestor
<!---->
The research mode began as a port of
[physics-intern](https://github.com/huggingface/physics-intern), which was built
for theoretical physics — a sub-agent derives a result and there is nothing to
look up.
This one is built for experimental data, where the work is calibrating
a detector and training a classifier on recorded waveforms, and the dominant
failure mode is guessing at a library API rather than making an algebra mistake.
<!---->
So the manager can read its own workspace and look up literature, sub-agents can
pull documentation, the reasoning and coding roles can run on different models,
and the nine-agent pipeline that came with the port was removed once the
Autophysicist carried its own critic and its own dispatch.
<!---->
The models it runs against are local: vLLM and a second engine on the
`son-of-anton` host, routed through a Bifrost proxy, with no request leaving the
network unless a hosted model is asked for by name.
<!---->
## Disclosure
<!---->
This project is developed with strong assistance from AI, with humans leading
the ideas, testing and debugging.
It is not my day job, and it is written that
way deliberately.
If you are not happy with AI-developed code guided by competent humans, this software is
not for you!!
