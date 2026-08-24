# Contributing

Use Python 3.10+, create a local virtual environment, install `.[dev]`, and run `pytest` before proposing changes. New behavior must start from a concrete consumer workflow and requires synthetic tests plus machine-readable output. Never commit user data, absolute user paths, serialized models, generated baselines, or domain-specific claims. Changes to status semantics must document backward compatibility and add gate tests.

Contributions are submitted under the Apache License, Version 2.0. Contributors must have the right to submit their code and documentation. Do not submit secrets, private data, restricted datasets, unlicensed third-party code, or project-specific data, results, or other assets. This project currently has no CLA or DCO process. New runtime dependencies and any third-party material with a NOTICE requirement require a fresh license review. Include appropriate tests and documentation with behavioral changes.
