{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.05";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
  };

  nixConfig = {
    extra-trusted-public-keys =
      "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs = { self, nixpkgs, devenv, systems, ... }@inputs:
    let forEachSystem = nixpkgs.lib.genAttrs (import systems);
    in {
      packages = forEachSystem (system: {
        devenv-up = self.devShells.${system}.default.config.procfileScript;
      });

      devShells = forEachSystem (system:
        let pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = devenv.lib.mkShell {
            inherit inputs pkgs;
            modules = [{
              # https://devenv.sh/reference/options/
              env.CELERY_CUSTOM_WORKER_POOL =
                "celery_async_threadpool:TaskPool";
              env.PYTHONDONTWRITEBYTECODE = "DONT";
              # packages = [ pkgs.hello ];
              languages.python.enable = true;
              languages.python.venv.enable = true;
              languages.python.venv.requirements = "  pdm\n";

              enterShell = ''
                pdm sync
              '';
              scripts.celery_worker.exec =
                "  celery -A tests.celery_app:app worker -c 1 -Pcustom --loglevel=INFO\n";

              # processes.run.exec = "hello";
            }];
          };
        });
    };
}
