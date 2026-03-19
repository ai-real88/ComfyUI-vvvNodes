# Recurring Issues and Solutions

## ComfyUI JavaScript Extension Imports

### Problem
When writing JavaScript extensions for ComfyUI, using relative paths like `../../scripts/app.js` often leads to `[vite:preloadError] TypeError: Failed to fetch dynamically imported module`. This happens because the frontend router or the way ComfyUI serves extension files doesn't always resolve relative paths consistently depending on the URL context.

### Solution
Always use absolute paths starting from the root for core ComfyUI scripts.
- **Incorrect:** `import { app } from "../../scripts/app.js";`
- **Correct:** `import { app } from "/scripts/app.js";`
- **Correct (widgets):** `import { ComfyWidgets } from "/scripts/widgets.js";`
