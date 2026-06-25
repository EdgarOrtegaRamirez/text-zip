# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

Please report security vulnerabilities via GitHub Issues. Do not open a public issue for security concerns.

## Security Design

TextZip is designed with security in mind:

1. **No network calls** - All compression is done locally with no external API dependencies
2. **No secrets** - No hardcoded tokens, keys, or credentials
3. **Input validation** - File paths are validated, text input is handled safely
4. **No code execution** - Compression strategies use regex and string operations only, no eval() or exec()
