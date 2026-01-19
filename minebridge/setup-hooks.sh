#!/bin/bash

echo "Setting up Git hooks..."

git config core.hooksPath .githooks

chmod +x .githooks/commit-msg

echo "Hooks successfully installed!"
