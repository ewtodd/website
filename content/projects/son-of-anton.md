---
title: "son-of-anton"
description: "An always-on agent you can talk to from a terminal or from Signal, with a physics research loop."
summary: "An always-on agent you can talk to from a terminal or from Signal, with a separate physics research loop that runs model-written code against the lab's data in a sandbox."
weight: 30
status: "Active"
role: "Author, hard fork"
license: "MIT"
stack: ["Python", "Textual", "Nix", "uv2nix"]
host: "e-desktop, against a local OpenAI-compatible endpoint"
repo: "https://github.com/ewtodd/son-of-anton"
lastmod: 2026-10-19
---
<!---->
An always-on agent you can talk to from a terminal or from Signal.
It has two modes: the normal agent loop, and a physics research loop.
<!---->
All chat runs one agent loop, with terminal, files, web, memory,
delegation and cron as its tools. One gateway process also runs the
cron scheduler, and a NixOS module runs one service per account so the
agent starts at boot without anyone logging in. The gateway and the
terminal share one `state.db`, so a conversation started on Signal is
sitting there in the CLI.
<!---->
It is a hard fork of [Nous Research's
hermes-agent](https://github.com/NousResearch/hermes-agent), stripped to an
always-on daemon. The agent loop, memory, session search and cron started as
upstream's and have been reworked since; upstream's skills system, plugin
system and Ink interface are gone, as are every messaging platform but Signal
and every model provider but an OpenAI-compatible endpoint.
The daemon design and permission modes come from the archived
[temple](https://github.com/ewtodd/temple) harness I ran before it.
<!---->
The terminal interface is a Textual application modelled on
[opencode](https://github.com/sst/opencode) — the design is theirs, the code
is a from-scratch port.
It is the only interface: there is no `--tui` flag and no fallback REPL.
<!---->
## The physics mode is explicit
<!---->
A message never starts a run by itself: there is no keyword routing.
`son-of-anton problem create` writes a spec for a dataset from a data
directory and a one-line goal, and `son-of-anton problem run` runs one.
In a chat session you just ask the agent to create a problem for a dataset
and run it; it drives the same subcommand through its terminal.
<!---->
The Autophysicist is one research manager with append-only memory, a
windowed scratchpad, a token budget and a `submit_final_answer` tool.
It dispatches ephemeral sub-agents that run code in a sandbox, in a
git-versioned scratch directory, with each iteration reviewed from outside
by a critic.
<!---->
## Where generated code actually runs
<!---->
The physics mode executes code the model wrote.
It does not run in the agent's own interpreter: that venv deliberately ships
no scientific stack, because the dependency scope rule is "only packages
every session uses" and most deployments never run a physics turn.
<!---->
Instead `physics.python` names a separate interpreter, and the code runs
under a [bubblewrap](https://github.com/containers/bubblewrap) sandbox: no
network, no `$HOME`, a cleared environment with no API keys, and a
filesystem holding only the interpreter's store paths (read-only), the run's
own workspace (read-write) and the lab's data (read-only).
<!---->
{{< terminal title="ewtodd@e-desktop — son-of-anton" >}}
$ nix build .#physics-runtime
# ROOT, analysis_utilities, NumPy, SciPy, SymPy, matplotlib,
# pandas, scikit-learn, xgboost, h5py
$ export SON_OF_ANTON_PHYSICS_PYTHON=./result/bin/python3
$ son-of-anton problem run problems/run42/problem.toml --max-iterations 5
sandbox: ~/lab-data mounted read-only · critic every iteration
<!---->
{{< /terminal >}}
<!---->
That runtime is built from the
[Analysis-Utilities]({{< relref "analysis-utilities" >}}) flake input rather
than from this project's nixpkgs, because that project asks downstream
flakes to leave its `nixpkgs` alone, and its Python package has to be paired
with the interpreter it was built against.
<!---->
## Why it diverged from its ancestor
<!---->
The Autophysicist mode began as a port of
[physics-intern](https://github.com/huggingface/physics-intern), which was
built for theoretical physics — a sub-agent derives a result and there is
nothing to look up.
This one is built for experimental data, where the work is calibrating
a detector and training a classifier on recorded waveforms, and the
dominant failure is guessing at a library API.
<!---->
So the manager can read its own workspace and look up literature,
sub-agents can pull documentation, and the reasoning and coding roles can
run on different models: the coding job routes to a second model, because
that is where the volume is.
The nine-agent pipeline that came with the port was removed once the
Autophysicist carried its own critic and its own dispatch.
<!---->
## Disclosure
<!---->
This project is developed with strong assistance from AI, with humans leading
the ideas, testing and debugging.
It is not my day job, and it is written that
way deliberately.
If you are not happy with AI-developed code guided by competent humans, this software is
not for you!!
