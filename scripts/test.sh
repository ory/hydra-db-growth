#!/usr/bin/env bash

docker-compose -f .docker/hydra-postgresql.yml \
 -f .docker/hydra-mysql.yml \
 -f .docker/hydra-db-growth-tester.yml \
 -f .docker/hydra-db-growth-server.yml \
 -f .docker/jaeger.yml \
 up --build --remove-orphans