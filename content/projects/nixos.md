---
title: "NixOS"
description: "One flake describing ten (for now) machines — router, bastion, storage, inference hosts, workstations and a kiosk — deployed with Colmena."
summary: "One flake describing ten machines: router, bastion, storage, inference hosts, workstations and a kiosk, all deployed from a single build host."
weight: 40
status: "Active"
role: "Author"
license: "MIT"
stack: ["Nix", "NixOS", "Colmena", "agenix", "Caddy"]
host: "10 hosts, x86_64 and aarch64"
repo: "https://github.com/ewtodd/NixOS"
---
<!---->
The configuration behind everything else on this site, including the machine
serving this page.
Ten hosts described by one flake: a router, an SSH bastion, a
storage server, two inference machines, a model-router host, four workstations
and a living-room kiosk.
<!---->
## How it is organised
<!---->
Three layers, and a host is the intersection of them.
`modules/` holds
system-level configuration, `home-manager/` holds user-level configuration, and
`hosts/<name>/` enables what that machine actually is.
<!---->
The connective tissue is a set of `systemOptions` flags.
A host declares its
owner, its device type and its graphics vendor, and the modules decide from
there which drivers, hardening and services follow.
Users get a **work**,
**play**, **root** or **server** profile, and package selection is gated on the
profile rather than repeated per machine.
<!---->
{{< terminal title="ewtodd@e-desktop — colmena" >}}
$ colmena apply --on @server
# build on e-desktop, push closures to the five servers
$ nrs 
# rebuild the workstation in front of me
10 hosts · 1 build host · 0 servers compiling

{{< /terminal >}}
<!---->
The hive reuses each host's NixOS modules rather than redefining them, so the
deployment and `nixosConfigurations` cannot drift. One workstation is the build
host and pushes results, which is why the servers and laptops never compile
anything themselves.
<!---->
## Services worth naming
<!---->
**Reverse proxy and TLS.** Caddy on the router terminates every public
hostname. This site and the [documentation]({{< param docsURL >}}) are static, so
Caddy serves their Nix store paths directly with no backend at all; the
interactive services sit behind a proof-of-work challenge.
<!---->
**Binary cache.** The workstation serves its own store over `nix-serve-ng`, and
every other host is configured against it. That is what makes a CUDA-overlaid
ROOT build practical: it is compiled once, on the machine with the GPU, and
fetched everywhere else.
<!---->
**Local inference.** Two engines on a dual-GPU host with a tensor-parallel
served model and a long-context vision model beside it, an aarch64 host running
the model router, a metasearch instance, and a gateway that aggregates the tool
servers. This is what [son-of-anton]({{< relref "son-of-anton" >}}) runs against.
<!---->
**The unglamorous half.** AdGuard and DNS, dynamic DNS for the apex and its
subdomains, Prometheus and Grafana, a ZFS pool with a Borg backup server,
Nextcloud, media, secrets with agenix, and a key-only deploy user whose sudo
rights stop at the activation commands.
<!---->
## Theming
<!---->
Colours come from `base16.nix` with schemes from `base16-schemes`, applied per
profile. The scheme is Kanagawa, which is where this site's palette and the one
in the generated API references both come from.
