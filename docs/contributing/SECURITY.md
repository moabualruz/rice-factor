# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

---

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Rice-Factor, please report it responsibly.

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email security concerns to: `security@rice-factor.dev`
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Timeline**: Depends on severity
  - Critical: 7 days
  - High: 14 days
  - Medium: 30 days
  - Low: 90 days

### Disclosure Policy

- We follow responsible disclosure
- Credit will be given to reporters (unless anonymity is requested)
- Security advisories will be published for significant vulnerabilities

---

## Security Considerations

### LLM API Keys

Rice-Factor requires API keys for LLM providers. These keys should be:

- Stored as environment variables, never in config files
- Never committed to version control
- Rotated regularly
- Limited in scope where possible

```bash
# Good: Environment variable
export ANTHROPIC_API_KEY=sk-...

# Bad: In config file (never do this)
# llm:
#   api_key: sk-...  # NEVER!
```

### Project Directory Security

The `.project/` directory contains:
- **requirements.md**: May contain sensitive project details
- **artifacts/**: Generated plans (may reference internal systems)
- **audit/**: Full audit trail of operations

Recommendations:
- Add `.project/` to `.gitignore` if it contains sensitive data
- Review artifacts before committing to public repos
- Use remote storage (S3/GCS) with proper IAM for team projects

### Authentication

The Web UI supports OAuth2 authentication:
- GitHub OAuth
- Google OAuth
- Anonymous mode (for local development)

For production deployments:
- Always use HTTPS
- Configure OAuth with proper redirect URLs
- Use session cookies with `HttpOnly` and `Secure` flags
- Implement CSRF protection

### Network Security

- By default, the Web UI binds to `localhost:8000`
- For remote access, use a reverse proxy (nginx, Caddy) with TLS
- API endpoints require authentication in production mode

### Code Execution

Rice-Factor can execute:
- Test commands (`pytest`, `npm test`, etc.)
- Refactoring tools (OpenRewrite, jscodeshift, etc.)
- Git operations

Security measures:
- Commands are never constructed from user input
- All execution is sandboxed to the project directory
- Dangerous operations require explicit `--yes` flag

### Dependency Security

We regularly audit dependencies:
- Python dependencies via `pip-audit`
- Node.js dependencies via `npm audit`
- Automated security updates via Dependabot

---

## Security Best Practices

### For Users

1. **Keep Rice-Factor updated** to receive security patches
2. **Protect API keys** - use environment variables, not config files
3. **Review generated code** before applying diffs
4. **Use authentication** when deploying Web UI
5. **Backup artifacts** before major operations

### For Contributors

1. **Never log secrets** - audit all log statements
2. **Validate inputs** - especially file paths and user inputs
3. **Use parameterized queries** - if adding database support
4. **Follow OWASP guidelines** - for web security
5. **Review dependencies** - check licenses and security history

---

## Known Security Considerations

### LLM Output

LLM-generated code may contain:
- Security vulnerabilities (SQL injection, XSS, etc.)
- Outdated patterns
- Incorrect error handling

Always:
- Review generated diffs carefully
- Run security linters on generated code
- Test thoroughly before deploying

### Artifact Storage

Artifacts stored in `.project/artifacts/` are JSON files:
- They may contain project structure information
- They may reference file paths
- They should not contain secrets

For sensitive projects, consider:
- Encrypting artifacts at rest
- Using remote storage with encryption
- Implementing access controls

---

## Contact

- Security issues: `security@rice-factor.dev`
- General inquiries: Open a GitHub issue
- Documentation: See [Contributing Guide](README.md)
