#!/usr/bin/env bash

docker-compose -f .docker/hydra-postgresql.yml \
 -f .docker/hydra-mysql.yml \
 -f .docker/hydra-db-growth-tester.yml \
 -f .docker/hydra-db-growth-server.yml \
 -f .docker/jaeger.yml \
kill

docker-compose -f .docker/hydra-postgresql.yml \
 -f .docker/hydra-mysql.yml \
 -f .docker/hydra-db-growth-tester.yml \
 -f .docker/hydra-db-growth-server.yml \
 -f .docker/jaeger.yml \
rm -f -v

rm ./test.db