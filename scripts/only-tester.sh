#!/usr/bin/env bash

docker-compose -f .docker/hydra-db-growth-server.yml \
  -f .docker/hydra-db-growth-tester.yml \
  up --build
