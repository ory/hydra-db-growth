#!/usr/bin/env bash

docker-compose -f .docker/setup.yml \
 -f .docker/hydra-postgresql.yml \
 -f .docker/hydra-mysql.yml \
 -f .docker/hydra-db-growth-tester.yml \
 -f .docker/hydra-db-growth-server.yml \
kill

docker-compose -f .docker/setup.yml \
 -f .docker/hydra-postgresql.yml \
 -f .docker/hydra-mysql.yml \
 -f .docker/hydra-db-growth-tester.yml \
 -f .docker/hydra-db-growth-server.yml \
rm -f -v