#!/bin/bash

# check-prerequisites.sh - Check prerequisites and return feature directory and available docs

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

# Find available documentation files
AVAILABLE_DOCS=()

if [[ -f "${FEATURE_DIR}spec.md" ]]; then
    AVAILABLE_DOCS+=("${FEATURE_DIR}spec.md")
fi

if [[ -f "${FEATURE_DIR}plan.md" ]]; then
    AVAILABLE_DOCS+=("${FEATURE_DIR}plan.md")
fi

if [[ -f "${FEATURE_DIR}data-model.md" ]]; then
    AVAILABLE_DOCS+=("${FEATURE_DIR}data-model.md")
fi

if [[ -f "${FEATURE_DIR}research.md" ]]; then
    AVAILABLE_DOCS+=("${FEATURE_DIR}research.md")
fi

if [[ -f "${FEATURE_DIR}quickstart.md" ]]; then
    AVAILABLE_DOCS+=("${FEATURE_DIR}quickstart.md")
fi

if [[ -d "${FEATURE_DIR}contracts" ]]; then
    for contract in "${FEATURE_DIR}contracts/"*; do
        if [[ -f "$contract" ]]; then
            AVAILABLE_DOCS+=("$contract")
        fi
    done
fi

# Output JSON configuration
printf '{\n'
printf '  "FEATURE_DIR": "%s",\n' "$FEATURE_DIR"
printf '  "AVAILABLE_DOCS": [\n'
for i in "${!AVAILABLE_DOCS[@]}"; do
    if [[ $i -eq $((${#AVAILABLE_DOCS[@]} - 1)) ]]; then
        printf '    "%s"\n' "${AVAILABLE_DOCS[$i]}"
    else
        printf '    "%s",\n' "${AVAILABLE_DOCS[$i]}"
    fi
done
printf '  ]\n'
printf '}\n'