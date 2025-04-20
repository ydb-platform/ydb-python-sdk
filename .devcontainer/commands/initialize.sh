#!/bin/bash
set -e

git config --local user.email "$(git config user.email)"
git config --local user.name "$(git config user.name)"
