{ pkgs }:
let
  python = pkgs.python310;
  buildPythonApplication = pkgs.python310Packages.buildPythonApplication;

  buildPythonDeps = with pkgs; [
    (python.withPackages (ps: with ps; [
      pip
      hatch
      hatchling
      tomli
      packaging
      pyproject-hooks
      build
    ]))
  ];

  propagatedPythonDeps = with pkgs; [
    (python.withPackages (ps: with ps; [
      pygobject3
      dbus-python
      pillow
      click
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
buildPythonApplication {
  pname = "notifd";
  version = "0.0.2";
  name = "notifd";
  src = ./..;
  format = "pyproject";

  doCheck = false;

  nativeBuildInputs = [
    pkgs.gobject-introspection
    pkgs.wrapGAppsHook
    buildPythonDeps
    nativeDeps
  ];

  propagatedBuildInputs = [ nativeDeps propagatedPythonDeps ];
}
