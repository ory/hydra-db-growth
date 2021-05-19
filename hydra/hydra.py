import os


def build_hydra():
    if os.path.isdir('.build'):
        os.system("cd .build/hydra; git checkout db-growth; git pull; go build -tags sqlite -o hydra")
    else:
        os.system("./scripts/build_hydra.sh")
