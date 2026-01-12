# F14.5-04: Configuration Schema - Tasks

> **Status**: Complete

---

## Tasks

### T14.5-04-01: Add parsing configuration section
- [x] Files: `rice_factor/config/defaults.yaml`
- Added `parsing` section with:
  - `provider`: treesitter | native | none
  - `fallback_to_regex`: true/false
  - `cache_parsed_files`: true/false
  - `max_file_size_kb`: file size limit

### T14.5-04-02: Add LSP configuration section
- [x] Files: `rice_factor/config/defaults.yaml`
- Added `lsp` section with:
  - `mode`: one_shot | persistent
  - `default_memory_limit_mb`: default limit
  - `default_timeout_seconds`: default timeout
  - `servers`: per-server configurations

### T14.5-04-03: Configure server defaults
- [x] Configured defaults for each server:
  - gopls: 2048MB, 60s timeout
  - rust-analyzer: 4096MB, 60s timeout
  - tsserver: 2048MB, 60s timeout
  - pylsp: 1024MB, 60s timeout

---

## Configuration Added

```yaml
parsing:
  provider: "treesitter"
  fallback_to_regex: true
  cache_parsed_files: true
  max_file_size_kb: 1024

lsp:
  mode: "one_shot"
  default_memory_limit_mb: 2048
  default_timeout_seconds: 60
  servers:
    gopls:
      command: ["gopls", "serve"]
      languages: ["go"]
      memory_limit_mb: 2048
      install_hint: "go install golang.org/x/tools/gopls@latest"
    rust_analyzer:
      command: ["rust-analyzer"]
      languages: ["rust"]
      memory_limit_mb: 4096
      install_hint: "rustup component add rust-analyzer"
    tsserver:
      command: ["typescript-language-server", "--stdio"]
      languages: ["typescript", "javascript"]
      memory_limit_mb: 2048
      install_hint: "npm install -g typescript-language-server"
    pylsp:
      command: ["pylsp"]
      languages: ["python"]
      memory_limit_mb: 1024
      install_hint: "pip install python-lsp-server"
```

---

## Files Modified

| File | Description |
|------|-------------|
| `rice_factor/config/defaults.yaml` | Added parsing and lsp sections |

---

## Estimated Test Count: ~5
## Actual Test Count: Config validated at runtime
