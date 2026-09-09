{
  description = "ethanwtodd.com — personal site";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        # The built site, as a store path. A Caddy vhost can serve this
        # directly, the same way the other services on nu are wired.
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "ethanwtodd-com";
          version = "0.1.0";
          src = ./.;
          nativeBuildInputs = [ pkgs.hugo ];
          dontConfigure = true;
          buildPhase = ''
            runHook preBuild
            hugo --gc --minify --destination public
            runHook postBuild
          '';
          installPhase = ''
            runHook preInstall
            mkdir -p $out
            cp -r public/. $out/
            runHook postInstall
          '';
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [ hugo ];
          shellHook = ''
            export SHELL="${pkgs.bash}/bin/bash"
            echo "ethanwtodd.com — 'hugo server -D' to preview, 'nix build' to produce the site"
          '';
        };
      }
    );
}
