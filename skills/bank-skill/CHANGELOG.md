# Changelog

All notable changes to the bank-skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-02-08

### Added
- Self-contained skill with embedded Python source code
- All bankskills modules included in skill directory
- pyproject.toml for dependency management

### Changed
- Made skill fully self-contained for direct GitHub installation
- Skill now works standalone without requiring project root

### Fixed
- Skill now includes all Python code needed to execute
- Fixed missing source code issue in skills.sh installations

## [0.1.3] - 2026-02-08

### Added
- README.md included in npm package
- Complete Python source code in package

## [0.1.2] - 2026-02-08

### Fixed
- Removed example-skill from distribution

## [0.1.1] - 2026-02-08

### Added
- README.md for npm package page
- Security section in documentation

## [0.1.0] - 2026-02-08

### Added
- Initial release
- Check balance operation
- Get receive details operation  
- Send money operation (USD ACH and EUR IBAN)
- MCP Desktop Extension (.mcpb)
- CLI interface
- MCP server interface
- Comprehensive test suite (127 tests)

### Security
- Environment variable-based API key management
- IP whitelisting support via Wise dashboard
- Token redaction in logs and error messages
