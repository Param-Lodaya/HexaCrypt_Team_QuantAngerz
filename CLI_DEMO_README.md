# HexaCrypt CLI Demonstrator

## Purpose

`cli.py` is a presentation/orchestration layer for the Code-V2 research
prototype. It does not replace or rewrite the mathematical modules.

The UI is intentionally designed for a hackathon demo video:

1. Initialize
2. Alice locks a generation
3. Bob transports a fresh session key
4. Alice recovers the key
5. Payload is encrypted
6. Doom / Release Gate decides whether data is released

## Run

From inside `Code-V2 - Copy`:

```bash
python cli.py
```

Direct showcase:

```bash
python cli.py demo
```

Faster video capture:

```bash
python cli.py demo --pace 0.20
```

Architecture-only:

```bash
python cli.py architecture
```

Validation summary:

```bash
python cli.py validation
```

The existing full numerical validation remains:

```bash
python test_hexacrypt.py
```

## Presentation philosophy

The CLI deliberately does **not** print:

- full matrices
- all 160 A2 coordinates
- every coefficient
- raw ciphertext arrays
- full mathematical derivations
- internal stack traces

Those details remain in the research/code artifacts.

The terminal shows the transformation and a small number of proof values:
fingerprints, dimensions, recovery equality, terminal value, and tamper result.

## Important research boundary

The current symmetric construction is an experimental research construction.
The CLI therefore labels HexaCrypt as a research prototype and does not claim
equivalence to AES-GCM or another standardized AEAD.
