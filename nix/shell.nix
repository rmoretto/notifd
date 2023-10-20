{ pkgs }:
let
  python = pkgs.python310;
  mkShell = pkgs.mkShell;

  pythonDeps = with pkgs; [
    (python.withPackages (ps: with ps; [
      pip
      hatch
      hatchling
      tomli
      packaging
      pyproject-hooks
      build
      pygobject3
      dbus-python
      pillow
      click
      twine
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
in 
mkShell {
  nativeBuildInputs = [
    pkgs.gobject-introspection
    pkgs.wrapGAppsHook
    nativeDeps
  ];

  buildInputs = [ nativeDeps pythonDeps ];

  shellHook = ''
    # HACK: go to the user defined shell
    $SHELL
  '';
}
