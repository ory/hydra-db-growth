#!/usr/bin/env bash

docker-compose -f .docker/hydra-postgresql.yml \
 -f .docker/hydra-mysql.yml \
 -f .docker/jaeger.yml \
 up --build