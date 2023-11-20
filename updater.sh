#!/usr/bin/env bash
git fetch --all
git reset --hard origin/main
sudo systemctl restart enviromental_logger.service