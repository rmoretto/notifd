{
  description = "notifd";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let 
        pkgs = nixpkgs.legacyPackages.${system}; 
        python = pkgs.python310;
        buildPythonApplication = pkgs.python310Packages.buildPythonApplication;

        buildPython = with pkgs; [
          (python.withPackages (ps: with ps; [
            pip
            hatch
            hatchling
            pygobject3
            dbus-python
            pillow
            click
            tomli
            packaging
            pyproject-hooks
            build
          ]))
        ];

        nativeDeps = [
          pkgs.pango
          pkgs.glib
          pkgs.gtk3
          pkgs.pkg-config
          pkgs.bashInteractive
          pkgs.ninja
        ];

        pythonDeps = [ 
          buildPython 
        ];
      in
      {
        defaultPackage = buildPythonApplication {
          pname = "notifd";
          name = "notifd";
          src = ./.;
          format = "pyproject";

          doCheck = false;

          nativeBuildInputs = [
            pkgs.gobject-introspection
            pkgs.wrapGAppsHook
            nativeDeps
          ];

          propagatedBuildInputs = [ nativeDeps pythonDeps ];
        };

        devShell = pkgs.mkShell {
          nativeBuildInputs = [
            pkgs.gobject-introspection
            pkgs.wrapGAppsHook
            nativeDeps
          ];
          buildInputs = [ nativeDeps pythonDeps ];
        };
      }
    );
}

