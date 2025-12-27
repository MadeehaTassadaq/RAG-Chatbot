#!/bin/bash

# setup-plan.sh - Setup planning environment and return JSON configuration

# Get the current repository root
REPO_ROOT=$(pwd)
BRANCH=$(git branch --show-current)

# Find the feature directory matching the branch pattern
FEATURE_DIR=""
for dir in specs/*/; do
    if [[ "$dir" == *"$BRANCH"* ]]; then
        FEATURE_DIR="$dir"
        break
    fi
done

if [[ -z "$FEATURE_DIR" ]]; then
    echo "Could not find feature directory matching current branch: $BRANCH" >&2
    exit 1
fi

FEATURE_SPEC="${FEATURE_DIR}spec.md"
IMPL_PLAN="${FEATURE_DIR}plan.md"

# Output JSON configuration
cat <<EOF
{
    "FEATURE_SPEC": "$FEATURE_SPEC",
    "IMPL_PLAN": "$IMPL_PLAN",
    "SPECS_DIR": "specs",
    "BRANCH": "$BRANCH",
    "REPO_ROOT": "$REPO_ROOT"
}
EOF