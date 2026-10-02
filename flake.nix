{
  description = "ethanwtodd.com — personal site and published documentation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    # The CV is written and versioned elsewhere, in LaTeX. Taking it as an
    # input rather than copying its contents here means /cv is generated from
    # the same source that produces CV.pdf, and updating the page is one
    # `nix flake update curriculum-vitae`. `flake = false` because only the
    # source tree is wanted: that repository's own flake is a texlive dev
    # shell, and nothing here builds the PDF (the repository commits it).
    curriculum-vitae = {
      url = "github:ewtodd/Curriculum-Vitae";
      flake = false;
    };

    analysis-utilities.url = "github:ewtodd/Analysis-Utilities";
    music.url = "github:ewtodd/MUSIC";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      curriculum-vitae,
      analysis-utilities,
      music,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };

        # Turns the CV repository into data/cv.json + static/cv/CV.pdf. Shared
        # by the package build and the dev shell so both produce the same page.
        cvImport = pkgs.writeShellApplication {
          name = "cv-import";
          runtimeInputs = [ pkgs.python3 ];
          text = ''
            python3 "''${SITE_ROOT:-.}/scripts/cv_import.py" "$@"
          '';
        };

        site = pkgs.stdenv.mkDerivation {
          pname = "ethanwtodd-com";
          version = "0.2.0";
          src = ./.;
          nativeBuildInputs = [
            pkgs.hugo
            pkgs.python3
          ];
          dontConfigure = true;

          # Recorded on the CV page so a reader can tell how current it is.
          cvRev = curriculum-vitae.rev or "";
          cvUpdated = curriculum-vitae.lastModifiedDate or "";

          buildPhase = ''
            runHook preBuild
            python3 scripts/cv_import.py ${curriculum-vitae} \
              --site . --rev "$cvRev" --updated "$cvUpdated"
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

        # Everything served at docs.ethanwtodd.com: the generated references
        # under a path prefix each, and this site's documentation index at the
        # root. Doxygen emits only relative links, which is what lets those
        # sites live under a prefix at all.
        #
        # The index is the page Hugo renders at /docs/ — a deliberately
        # self-contained one, with its CSS inlined and its links absolute, so
        # the identical file is correct on both hostnames.
        #
        # The theme is applied here, and lives nowhere else. Neither project
        # carries a stylesheet of its own: they build as plain doxygen-awesome,
        # which is what you read warnings against, and the published reference
        # gets its design when this derivation assembles the host. The
        # dependency runs one way only — this flake has both projects as inputs
        # and neither knows this repository exists — so the design changes here,
        # once, for all of them.
        #
        # Doxygen has no hook for adding a stylesheet after the fact, so the
        # link is inserted into the generated pages. The anchor is the closing
        # </head>, which puts this stylesheet last in the cascade and therefore
        # ahead of anything a project might ship of its own — so the published
        # look does not depend on the projects being updated in step with this
        # repository. It is checked rather than assumed: every page doxygen
        # writes has exactly one, and the build fails if any page is missed.
        docsTheme = ./assets/css/doxygen.css;

        docs = pkgs.runCommand "ethanwtodd-docs" { } ''
          mkdir -p $out/analysis-utilities $out/music
          cp -r ${site}/docs/. $out/
          cp -r ${analysis-utilities.packages.${system}.docs}/. $out/analysis-utilities/
          cp -r ${music.packages.${system}.docs}/. $out/music/
          chmod -R u+w $out

          for project in analysis-utilities music; do
            cp ${docsTheme} "$out/$project/ethanwtodd.css"

            mapfile -t pages < <(find "$out/$project" -name '*.html')
            if [ ''${#pages[@]} -eq 0 ]; then
              echo "$project: no generated pages to theme." >&2
              exit 1
            fi

            for page in "''${pages[@]}"; do
              if ! grep -qF '</head>' "$page"; then
                echo "$project: $(basename "$page") has no </head> to anchor" \
                     "the stylesheet to." >&2
                exit 1
              fi
              ${pkgs.gnused}/bin/sed -i \
                's|</head>|<link href="ethanwtodd.css" rel="stylesheet" type="text/css"/></head>|' \
                "$page"
            done

            themed=$(grep -rlF 'href="ethanwtodd.css"' "$out/$project" --include='*.html' | wc -l)
            if [ "$themed" -ne ''${#pages[@]} ]; then
              echo "$project: themed $themed of ''${#pages[@]} pages." >&2
              exit 1
            fi
            echo "$project: themed $themed pages"
          done
        '';
      in
      {
        # The built site, as a store path. A Caddy vhost can serve this
        # directly, the same way the other services on nu are wired.
        packages.default = site;
        packages.docs = docs;
        packages.cv-import = cvImport;

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.hugo
            pkgs.python3
            cvImport
          ];
          # A local checkout is the default source so the CV page can be worked
          # on without a flake update round-trip; the pinned input is the
          # fallback, and is what `nix build` always uses.
          CV_SOURCE_LOCAL = "../Curriculum-Vitae";
          CV_SOURCE_PINNED = "${curriculum-vitae}";
          shellHook = ''
            export SHELL="${pkgs.bash}/bin/bash"
            export SITE_ROOT="$PWD"
            if [ -d "$CV_SOURCE_LOCAL" ]; then
              export CV_SOURCE="$CV_SOURCE_LOCAL"
            else
              export CV_SOURCE="$CV_SOURCE_PINNED"
            fi
            echo "ethanwtodd.com"
            echo "  cv-import       — regenerate data/cv.json from $CV_SOURCE"
            echo "  hugo server -D  — preview"
            echo "  nix build       — the site"
            echo "  nix build .#docs — docs.ethanwtodd.com, references included"
          '';
        };
      }
    );
}
