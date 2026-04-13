# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Portainer Quick is a PyQt6 desktop GUI for managing Docker stacks via the Portainer API. It lets users view, start, and stop stacks across one or more Portainer instances.

## Running

```bash
python3 portainer_quick.py
```

Requires a config file at `~/.config/portainer-quick/config.json` (auto-created on first run with placeholder values). The config defines Portainer instances with `name`, `url`, `apiKey`, and `environmentId`.

## Installation

```bash
chmod +x install.sh
./install.sh YOUR_API_KEY
```

This copies the script to `~/.local/share/portainer-quick/`, installs a launcher script to `~/.local/bin/portainer-quick`, registers a `.desktop` file, and runs `pip3 install PyQt6`.

## Dependencies

- Python 3
- PyQt6 (GUI framework)
- requests (HTTP client for Portainer API)

## Architecture

Single-file application (`portainer_quick.py`) with three layers:

- **Data model**: `StackStatus` enum and `Stack` class representing a Docker stack's state
- **API client**: `PortainerClient` class — communicates with Portainer REST API (`/api/stacks`, start/stop endpoints) using API key auth via `X-API-Key` header
- **GUI**: PyQt6 widgets — `StackItem` (per-stack row with start/stop button), `window` (main window with scroll area, sync button, optional instance filter combo box, 5-second auto-refresh timer)

Config is loaded at module level: reads `~/.config/portainer-quick/config.json`, deserializes instances into `SimpleNamespace` objects, validates required fields, then creates a global `PortainerClient` and launches the Qt app.

## Portainer API

All requests use `verify=False` (no SSL verification). Authentication is via `X-API-Key` header. Key endpoints:
- `GET /api/stacks` — list stacks
- `POST /api/stacks/{id}/start?endpointId={envId}` — start a stack
- `POST /api/stacks/{id}/stop?endpointId={envId}` — stop a stack
