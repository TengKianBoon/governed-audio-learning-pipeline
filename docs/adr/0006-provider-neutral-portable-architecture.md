# ADR-0006: Provider-Neutral Portable Architecture

Date: 2026-06-20  
Status: accepted

## Context

The project will be evaluated publicly by enterprise AI practitioners and technical readers. Vendor lock-in, hidden paid dependencies, and cloud-only assumptions would weaken the architecture and could expose the owner's learning data.

## Decision

Keep providers configurable and replaceable. Use local filesystem storage, local/free transcription, and MCP-ready tool boundaries for MVP. Treat vendors as research subjects unless explicitly approved as runtime providers.

## Why

This protects portability, cost control, privacy, and long-term maintainability. It also demonstrates enterprise AI judgment: choose providers deliberately, not accidentally.

## Consequences

Provider-specific integrations require an ADR, budget review, privacy review, and a fallback path before becoming default.
