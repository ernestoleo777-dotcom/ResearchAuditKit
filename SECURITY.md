# Security

Report path traversal, unsafe overwrite, untrusted deserialization, or privacy issues privately to the repository maintainer. ResearchAuditKit does not deserialize model objects or execute audited repository code. Treat policies and CSV/JSON/YAML inputs as untrusted: run the CLI with the minimum filesystem permissions needed and inspect output paths before use.

