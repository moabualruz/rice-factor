# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Rice-Factor, please report it responsibly.

### How to Report

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please report security issues via:

1. **Email**: security@rice-factor.dev (preferred)
2. **GitHub Security Advisories**: [Report a vulnerability](https://github.com/user/rice-factor/security/advisories/new)

### What to Include

Please include:

1. **Description**: Clear description of the vulnerability
2. **Impact**: Potential impact and severity assessment
3. **Steps to Reproduce**: Detailed steps to reproduce the issue
4. **Proof of Concept**: If possible, include PoC code
5. **Suggested Fix**: If you have ideas for remediation

### Response Timeline

| Action | Timeline |
|--------|----------|
| Acknowledgment | Within 48 hours |
| Initial Assessment | Within 1 week |
| Status Update | Every 2 weeks |
| Fix Release | Depends on severity |

### Severity Levels

| Level | Description | Response |
|-------|-------------|----------|
| Critical | Remote code execution, data breach | Immediate patch |
| High | Privilege escalation, significant data exposure | Patch within 7 days |
| Medium | Limited data exposure, DoS | Patch within 30 days |
| Low | Minor issues, hardening | Next regular release |

## Security Considerations

### LLM API Keys

Rice-Factor handles LLM API keys. Best practices:

- **Never commit API keys** to version control
- Use environment variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
- Use `.env` files with `.gitignore`
- Rotate keys regularly

```bash
# Good: Environment variable
export ANTHROPIC_API_KEY=sk-ant-...

# Bad: In code or config files (committed)
api_key: sk-ant-...  # NEVER DO THIS
```

### Artifact Storage

Artifacts may contain sensitive information:

- **Project plans** may reveal architecture
- **Implementation plans** contain code logic
- **Test plans** may expose business rules

Recommendations:
- Restrict `.project/artifacts/` access
- Use remote storage with encryption for teams
- Audit artifact access in production

### Code Execution

Rice-Factor executes code through:
- Test runners (`pytest`, `go test`, etc.)
- Refactoring tools
- Diff application

Mitigations:
- Sandboxed execution where possible
- Human approval required for all changes
- Audit trail of all executions

### Input Validation

All inputs are validated:
- Artifact payloads against JSON Schema
- CLI arguments via Typer
- Configuration via Pydantic/Dynaconf

### Dependencies

We monitor dependencies for vulnerabilities:
- Automated dependency updates (Dependabot)
- Regular security audits
- Minimal dependency surface

## Security Features

### Artifact Integrity

- Artifacts are immutable once approved
- TestPlan locking prevents modification
- Audit trail tracks all changes

### Human-in-the-Loop

- All code changes require human approval
- LLM cannot write to disk directly
- Review step before applying diffs

### Audit Trail

- All operations logged
- Append-only audit log
- Traceable artifact history

## Hardening Recommendations

### Production Deployment

```yaml
# .rice-factor.yaml - Production settings
security:
  # Require explicit approval for all operations
  require_approval: true

  # Enable audit logging
  audit_enabled: true
  audit_level: detailed

  # Restrict LLM operations
  llm:
    max_tokens: 4096
    rate_limit: 60/minute
```

### Network Security

- Use HTTPS for all API calls
- Configure firewall rules for local LLM servers
- Use VPN for remote storage access

### Access Control

- Implement role-based access for teams
- Use separate API keys per environment
- Rotate credentials regularly

## Known Limitations

1. **LLM Outputs**: LLM-generated content is not guaranteed to be secure
2. **Local Storage**: Default filesystem storage is not encrypted
3. **Trust Boundary**: Approved artifacts are trusted for execution

## Security Updates

Security updates are announced via:
- GitHub Security Advisories
- Release notes
- Project mailing list (TBD)

## Acknowledgments

We thank the security researchers who have helped improve Rice-Factor's security:

- (Your name could be here)

## Contact

- Security issues: security@rice-factor.dev
- General questions: [GitHub Discussions](https://github.com/user/rice-factor/discussions)
