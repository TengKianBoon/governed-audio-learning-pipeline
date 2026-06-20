# ADR-0003: Manual-First Agentic Build

Date: 2026-06-20  
Status: accepted

## Context

The goal is to demonstrate best-in-class enterprise AI development without over-automating before the verifier is trusted.

## Decision

Start manual-first: the human triggers runs, reviews quality gates, approves public publishing, and owns merge-to-main. Add multi-agent and scheduled automation only after the vertical slice is reliable.

## Why

This keeps learning visible, controls token/cost risk, and creates a stronger public technical narrative around earned autonomy.

## Consequences

The app includes agent contracts, hooks, and scoring now, but full automation is a later phase.
