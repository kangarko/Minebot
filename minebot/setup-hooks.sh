#!/bin/bash

echo "Setting up Git hooks..."

git config core.hooksPath .githooks

chmod +x .githooks/commit-msg
chmod +x .githooks/post-commit
chmod +x .githooks/pre-commit

echo "Hooks successfully installed!"
