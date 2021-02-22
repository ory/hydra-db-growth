#!/usr/bin/env bash

docker-compose -f .docker/hydra-db-growth-tester.yml \
 -f .docker/hydra-db-growth-server.yml \
  up --build
