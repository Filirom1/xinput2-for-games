{
  description = "XInput2 CLI/GUI tool for multiplayer gaming setup on Linux";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        python = pkgs.python3;
        
        xinput2-for-games = python.pkgs.buildPythonApplication {
          pname = "xinput2-for-games";
          version = "0.1.0";
          pyproject = true;

          src = ./.;

          build-system = with python.pkgs; [
            setuptools
            wheel
          ];

          dependencies = with python.pkgs; [
            xlib
            pygobject3
          ];

          nativeBuildInputs = [
            pkgs.gobject-introspection
            pkgs.wrapGAppsHook3
          ];

          buildInputs = [
            pkgs.gtk3
            pkgs.glib
          ];

          # Don't wrap twice
          dontWrapGApps = true;
          
          preFixup = ''
            makeWrapperArgs+=("''${gappsWrapperArgs[@]}")
          '';

          meta = with pkgs.lib; {
            description = "XInput2 CLI/GUI tool for multiplayer gaming setup on Linux";
            homepage = "https://github.com/Filirom1/xinput2-for-games";
            license = licenses.mit;
            platforms = platforms.linux;
            mainProgram = "xinput2-for-games";
          };
        };
      in
      {
        packages = {
          default = xinput2-for-games;
          xinput2-for-games = xinput2-for-games;
        };

        apps.default = {
          type = "app";
          program = "${xinput2-for-games}/bin/xinput2-for-games";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            python.pkgs.xlib
            python.pkgs.pygobject3
            pkgs.gtk3
            pkgs.gobject-introspection
            pkgs.xorg.xinput
          ];
          
          shellHook = ''
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
            echo "xinput2-for-games development shell"
            echo "Run: python -m xinput2_for_games.main --gui"
          '';
        };
      }
    ) // {
      overlays.default = final: prev: {
        xinput2-for-games = self.packages.${prev.system}.xinput2-for-games;
      };
      
      nixosModules.default = { config, lib, pkgs, ... }:
        let
          cfg = config.programs.xinput2-for-games;
        in
        {
          options.programs.xinput2-for-games = {
            enable = lib.mkEnableOption "xinput2-for-games multiplayer input setup tool";
          };

          config = lib.mkIf cfg.enable {
            environment.systemPackages = [
              self.packages.${pkgs.system}.xinput2-for-games
            ];
          };
        };
    };
}
