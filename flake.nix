{
  description = "Simple DBus notification watcher service";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=nixpkgs-unstable";
  };

  outputs = { self, nixpkgs, flake-utils }: let
    systems = [ "x86_64-linux" "aarch64-linux" ];
    forAllSystems = nixpkgs.lib.genAttrs systems;
  in rec {
    packages = forAllSystems (system: {
      default = nixpkgs.legacyPackages.${system}.callPackage ./nix/default.nix { };
    });

    devShells = forAllSystems (system: {
      default = nixpkgs.legacyPackages.${system}.callPackage ./nix/shell.nix { };
    });
  };
}
