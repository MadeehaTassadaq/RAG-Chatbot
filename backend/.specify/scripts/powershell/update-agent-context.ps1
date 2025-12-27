#!/usr/bin/env pwsh

# update-agent-context.ps1 - Update agent-specific context file

param(
    [string]$AgentType = "claude"
)

$repoRoot = Get-Location
$specDir = Join-Path $repoRoot "specs"
$branch = git branch --show-current

# Find the current feature directory
$featureDir = Get-ChildItem -Path $specDir -Directory | Where-Object { $branch -like "*$($_.Name)*" } | Select-Object -First 1

if ($null -ne $featureDir) {
    $planFile = Join-Path $featureDir.FullName "plan.md"

    if (Test-Path $planFile) {
        $planContent = Get-Content $planFile -Raw

        # Update agent context based on agent type
        switch ($AgentType) {
            "claude" {
                $agentContextFile = Join-Path $repoRoot ".claude/agent-context.md"
                if (!(Test-Path (Split-Path $agentContextFile -Parent))) {
                    New-Item -ItemType Directory -Path (Split-Path $agentContextFile -Parent) -Force
                }

                # Create or update the agent context file
                $contextContent = @"
# Agent Context for $branch

## Current Implementation Plan

$planContent

## Technology Stack
- FastAPI
- OpenAI SDK (with Gemini)
- Neon Postgres
- Qdrant Vector Database
- Cohere for embeddings
"@
                Set-Content -Path $agentContextFile -Value $contextContent
                Write-Output "Updated Claude agent context at $agentContextFile"
            }
            Default {
                Write-Output "Agent type $AgentType not supported yet"
            }
        }
    } else {
        Write-Warning "Plan file not found at $planFile"
    }
} else {
    Write-Warning "Could not find feature directory for branch $branch"
}