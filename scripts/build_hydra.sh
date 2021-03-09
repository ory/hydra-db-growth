rm -rf .build
mkdir .build; cd .build
git clone git@github.com:Benehiko/hydra.git
cd hydra
git checkout db-growth
go build -o hydra