# Customize Templates

This guide explains how to customize the project templates used by Rice-Factor.

## Overview

When you run `rice-factor init`, it creates template files in `.project/`. You can customize these templates to match your organization's standards.

## Default Templates

Rice-Factor creates these files:

```
.project/
├── requirements.md      # Project requirements
├── constraints.md       # Technical constraints
├── glossary.md          # Domain terminology
├── non_goals.md         # Explicit non-goals
└── risks.md             # Known risks
```

## Customizing Init Templates

### Method 1: Global Templates

Create templates in your user config directory:

```bash
# Linux/macOS
mkdir -p ~/.rice-factor/templates

# Windows
mkdir %USERPROFILE%\.rice-factor\templates
```

Create your custom templates:

```bash
# ~/.rice-factor/templates/requirements.md
# Project Requirements

## Overview
[Project description]

## Functional Requirements
| ID | Description | Priority |
|----|-------------|----------|
| FR-1 | | |

## Non-Functional Requirements
| ID | Description | Priority |
|----|-------------|----------|
| NFR-1 | | |

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

### Method 2: Project Templates

Include templates in your repository for team sharing:

```
my-org-templates/
├── .rice-factor/
│   └── templates/
│       ├── requirements.md
│       ├── constraints.md
│       └── ...
└── README.md
```

Then copy when starting a new project:

```bash
cp -r my-org-templates/.rice-factor .
rice-factor init  # Will use existing templates
```

## Template Variables

Templates support placeholder variables (future feature):

```markdown
# ${PROJECT_NAME} Requirements

Created: ${DATE}
Author: ${AUTHOR}

## Overview
${PROJECT_DESCRIPTION}
```

## Custom Template Examples

### Enterprise Requirements Template

```markdown
# Project Requirements

## Document Control
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | | | Initial |

## Executive Summary
[Brief description for stakeholders]

## Scope
### In Scope
-

### Out of Scope
-

## Functional Requirements

### User Stories
| ID | As a... | I want to... | So that... | Priority |
|----|---------|--------------|------------|----------|
| US-1 | | | | |

### Use Cases
#### UC-1: [Name]
- **Actor**:
- **Precondition**:
- **Main Flow**:
- **Postcondition**:

## Non-Functional Requirements

### Performance
- Response time:
- Throughput:

### Security
- Authentication:
- Authorization:

### Scalability
- Expected load:
- Growth projections:

## Dependencies
| Dependency | Version | Purpose |
|------------|---------|---------|
| | | |

## Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| | | | |

## Sign-off
| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Tech Lead | | | |
```

### Startup Constraints Template

```markdown
# Technical Constraints

## Language & Framework
- Language: Python 3.11+
- Framework: FastAPI
- Database: PostgreSQL

## Architecture
- Style: Microservices
- Communication: REST + gRPC
- Deployment: Kubernetes

## Quality Requirements
- Test coverage: > 80%
- Code review: Required
- CI/CD: GitHub Actions

## Third-Party Services
| Service | Purpose | Alternative |
|---------|---------|-------------|
| AWS S3 | Storage | MinIO |
| Stripe | Payments | - |

## Cost Constraints
- Monthly infra budget: $X
- Prefer open-source when possible
```

### Glossary Template with Categories

```markdown
# Domain Glossary

## Business Terms
| Term | Definition | Related Terms |
|------|------------|---------------|
| | | |

## Technical Terms
| Term | Definition | Related Terms |
|------|------------|---------------|
| | | |

## Acronyms
| Acronym | Full Form | Context |
|---------|-----------|---------|
| | | |

## User Roles
| Role | Description | Permissions |
|------|-------------|-------------|
| | | |
```

## Template Best Practices

### 1. Be Specific
Include placeholders for important information:

```markdown
## Performance Requirements
- API response time: ___ms (p95)
- Database query time: ___ms (p95)
- Concurrent users: ___
```

### 2. Add Guidance
Include instructions within templates:

```markdown
## Non-Goals
<!-- List things explicitly OUT of scope -->
<!-- This prevents scope creep and sets expectations -->

- Example: Mobile app support (web-only for MVP)
```

### 3. Categorize Risks

```markdown
## Risks

### Technical Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|

### Business Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|

### External Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
```

### 4. Version Control

Include templates in your team's shared repository:

```
team-standards/
├── rice-factor-templates/
│   ├── requirements.md
│   ├── constraints.md
│   └── ...
└── README.md
```

## Questionnaire Customization

The init questionnaire can also be customized (future feature):

```yaml
# ~/.rice-factor/questionnaire.yaml
questions:
  - id: project_type
    text: "What type of project is this?"
    options:
      - API Service
      - CLI Tool
      - Library
      - Full-Stack App

  - id: team_size
    text: "Team size?"
    options:
      - Solo
      - Small (2-5)
      - Medium (6-15)
      - Large (15+)
```

## What's Next?

- [First Project](../getting-started/first-project.md) - Use your templates
- [Configuration Reference](../../reference/configuration/settings.md) - All config options
