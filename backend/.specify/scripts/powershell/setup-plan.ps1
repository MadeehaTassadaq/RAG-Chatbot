#!/usr/bin/env pwsh

# setup-plan.ps1 - Setup planning environment and return JSON configuration

param(
    [switch]$Json
)

# Get the current repository root
$repoRoot = Get-Location

# Define the feature branch and spec path
$branch = git branch --show-current
$specsDir = Join-Path $repoRoot "specs"
$featureDir = Get-ChildItem -Path $specsDir -Directory | Where-Object { $branch -like "*$($_.Name)*" } | Select-Object -First 1

if ($null -eq $featureDir) {
    Write-Error "Could not find feature directory matching current branch: $branch"
    exit 1
}

$featureSpec = Join-Path $featureDir.FullName "spec.md"
$implPlan = Join-Path $featureDir.FullName "plan.md"

# Create the output object
$output = @{
    FEATURE_SPEC = $featureSpec
    IMPL_PLAN = $implPlan
    SPECS_DIR = $specsDir
    BRANCH = $branch
    REPO_ROOT = $repoRoot
}

if ($Json) {
    $output | ConvertTo-Json
} else {
    Write-Output "Feature Spec: $($output.FEATURE_SPEC)"
    Write-Output "Impl Plan: $($output.IMPL_PLAN)"
    Write-Output "Specs Dir: $($output.SPECS_DIR)"
    Write-Output "Branch: $($output.BRANCH)"
}