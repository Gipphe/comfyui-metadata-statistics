{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs =
    { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            (pkgs.python312.withPackages (
              ps: with ps; [
                bump-my-version
                coverage # testing
                mypy # linting
                pre-commit-hooks # runs linting on commit
                pytest # testing
                ruff # linting
              ]
            ))
          ];
        };
      }
    );
}
