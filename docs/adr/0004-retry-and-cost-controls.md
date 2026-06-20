# ADR-0004: Retry And Token Budget Controls

Date: 2026-06-20  
Status: accepted

## Context

Enterprise AI development must control reliability and cost. Infinite retries waste time and API calls. Large transcripts can also create hidden token spend once research or paid AI stages are added.

## Decision

Set retry max to 3 in config, use capped retries for external tool calls, and generate `cost_budget.json` for each learning package with rough token estimates and warning status.

## Why

This keeps the local MVP free-first while making future API use observable and governable.

## Consequences

Failures stop after 3 attempts and escalate. Future research agents must read `cost_budget.json` before making paid calls.
