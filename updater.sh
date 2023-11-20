#!/usr/bin/env bash
git fetch --all
git reset --hard origin/main
sudo systemctl restart enable enviromental_logger.service