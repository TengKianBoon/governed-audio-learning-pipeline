# ADR-0002: FFmpeg Configured, Not Globally Installed

Date: 2026-06-20  
Status: accepted

## Context

Another local application already uses FFmpeg. A second global install or PATH change could make debugging harder.

## Decision

This app uses FFmpeg and FFprobe through configured executable paths or an isolated portable copy. It does not modify global PATH.

## Why

FFmpeg is required for phone audio and local video handling, but it should not disturb other applications.

## Consequences

The first real run needs `ffmpeg_path` and `ffprobe_path` configured or available through a local command.
