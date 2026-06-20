# ADR-0005: MCP-First Interface, CLI As Fallback

Date: 2026-06-20  
Status: accepted

## Context

The project should showcase enterprise AI orchestration and tool integration. A CLI is useful for beginners, but MCP is a better long-term interface for agents, IDEs, and orchestrators.

## Decision

Expose core actions as MCP-ready tools first: process learning audio, review mindmap, sanitize public outputs, and read retry/cost policy. Keep the CLI as a thin wrapper around those tools.

## Why

This lets future agents call typed tools instead of shelling out, while preserving beginner-friendly manual commands.

## Consequences

The app has `app/mcp_tools.py` as the stable tool layer and `app/mcp_server.py` as an optional adapter for the Python MCP SDK.
