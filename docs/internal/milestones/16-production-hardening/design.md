# Milestone 16: Production Hardening - Design

> **Status**: Planned
> **Priority**: P0

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Production Infrastructure                     │
├─────────────────────────────────────────────────────────────────┤
│  Rate Limiter                                                    │
│    ├── Token bucket algorithm                                    │
│    └── Per-provider limits                                       │
├─────────────────────────────────────────────────────────────────┤
│  Storage Adapters                                                │
│    ├── FilesystemStorage (existing)                              │
│    ├── S3Storage (NEW)                                           │
│    └── GCSStorage (NEW)                                          │
├─────────────────────────────────────────────────────────────────┤
│  Notifications                                                   │
│    ├── WebhookAdapter                                            │
│    ├── SlackAdapter                                              │
│    └── TeamsAdapter                                              │
├─────────────────────────────────────────────────────────────────┤
│  Metrics                                                         │
│    ├── PrometheusExporter                                        │
│    └── OpenTelemetryExporter                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Package Structure

```
rice_factor/domain/services/
├── rate_limiter.py              # NEW
└── cost_tracker.py              # NEW

rice_factor/adapters/storage/
├── s3_adapter.py                # NEW
└── gcs_adapter.py               # NEW

rice_factor/adapters/notifications/
├── webhook_adapter.py           # NEW
├── slack_adapter.py             # NEW
└── teams_adapter.py             # NEW

rice_factor/adapters/metrics/
├── prometheus_adapter.py        # NEW
└── opentelemetry_adapter.py     # NEW
```
