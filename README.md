# HexaCrypt

### Experimental Hybrid Lattice Cryptography Research Prototype

> **Research prototype - not production-ready cryptography.**
> HexaCrypt explores a proposed key-establishment pipeline combining a
> secret-derived mathematical function, Learning With Errors (LWE)-style
> operations, an (A_2) hexagonal-lattice encoding/decoding experiment,
> Reed-Solomon redundancy, simulator-generated quantum measurements,
> and an experimental chained symmetric-encryption/release-gate design.

HexaCrypt is built to make a research idea testable: inspect the
mathematical stages, run a reproducible end-to-end experiment, observe
key-recovery and tamper-detection behaviour, and identify what still
needs rigorous analysis before any real-world use.

## Contents

-   [Why HexaCrypt?](#why-hexacrypt)
-   [What it does](#what-it-does)
-   [How the pipeline works](#how-the-pipeline-works)
-   [Architecture and modules](#architecture-and-modules)
-   [What the prototype has
    demonstrated](#what-the-prototype-has-demonstrated)
-   [Quick start](#quick-start)
-   [Run the experiments](#run-the-experiments)
-   [Expected behaviour](#expected-behaviour)
-   [Limitations and security status](#limitations-and-security-status)
-   [Roadmap](#roadmap)
-   [Repository structure](#repository-structure)
-   [Contributing and responsible
    use](#contributing-and-responsible-use)

## Why HexaCrypt?

Cryptographic research is easier to evaluate when a proposed
construction is expressed as a pipeline with code and observable
checks, not only as equations. HexaCrypt was created to explore a
hybrid design and to test several linked ideas together:

-   Deriving generation-specific private mathematical parameters from a
    long-term secret.
-   Constructing a secret vector using discrete integration and a
    forward-difference operation.
-   Experimenting with LWE-style public-key operations and noisy message
    recovery.
-   Encoding a 256-bit session key into (A_2) lattice symbols, with
    Reed--Solomon redundancy and nearest-point decoding.
-   Using a Qiskit **simulator** to generate measurement outcomes for
    coefficient and session-key bytes.
-   Demonstrating an experimental symmetric encryption chain whose final
    integrity check controls whether plaintext is returned.

The aim is **exploration and validation**, not a claim that a new secure
cryptographic primitive has been established.

## What it does

The current codebase contains a Python research implementation and
command-line demonstrator. At a high level, it can:

1.  Derive a generation seed and parameters from a fresh 32-byte secret.
2.  Construct a private function and derive a modular secret vector.
3.  Generate an LWE-style public component.
4.  Generate a 32-byte session key using a Qiskit Aer quantum-circuit
    simulator.
5.  Apply Reed-Solomon encoding, map the encoded bits to (A_2)
    coordinates, and pass the representation through an LWE-style
    encapsulation/decapsulation experiment.
6.  Attempt to recover the encoded key and report whether it matches.
7.  Encrypt a sample payload using the project's experimental
    SHA-512/XOR chained construction.
8.  Check a terminal hash value before returning decrypted plaintext;
    tampering should cause a failure instead of a successful return.

These are prototype behaviours. They do **not** establish
production-grade confidentiality, authenticity, quantum security, or
formal correctness.

## How the pipeline works

``` text
Long-term secret (SK_A)
        |
        v
Generation-specific KDF seed
        |
        v
Private-function parameters + simulator-generated coefficients
        |
        v
Discrete integration / forward difference
        |
        v
Secret vector s  -----> LWE-style public component (A, b, q)
                                  |
                                  v
                         Session key K (32 bytes)
                                  |
                                  v
                     Reed–Solomon encoding (40 bytes)
                                  |
                                  v
                     2-bit symbols mapped to A2 points
                                  |
                                  v
                    LWE-style encapsulation / recovery
                                  |
                                  v
                         Recovered-key comparison
                                  |
                                  v
                    Experimental symmetric encryption
                                  |
                                  v
                    Terminal-value verification gate
                          /                 \
                    match / valid       mismatch / tampered
                        |                      |
                  Return plaintext       Raise an error
```

### Stage 1 --- Generation and secret-vector construction

-   `math_core.py` derives a generation seed using HKDF-SHA256 and a
    generation identifier.
-   It derives parameters for a private function and evaluates that
    function using Python's high-precision `Decimal` arithmetic.
-   `compute_secret_vector()` applies the project's
    discrete-integration/forward-difference construction and reduces the
    resulting values modulo (q).
-   The code checks function monotonicity/stability as an empirical
    property of the generated function.

### Stage 2 --- LWE-style operations

-   `lwe_engine.py` implements key-component generation, encapsulation,
    and decapsulation using matrix/vector arithmetic modulo (q).
-   The current experiment uses parameters such as (q = 1{,}048{,}576),
    (n = 64), and (m = 128).
-   Noise values and message scaling influence whether decoding
    succeeds. The implementation is a research experiment; its
    parameters and distributions are not presented as a standardized or
    security-reviewed scheme.

### Stage 3 --- Session-key encoding and (A_2) decoding

-   `quantum_rng.py` uses Qiskit Aer's `AerSimulator` to sample
    measurement outcomes from Hadamard-gate circuits. **This is
    simulated quantum measurement, not a physical quantum random-number
    generator.**
-   `encoding.py` adds Reed--Solomon redundancy to a 32-byte session
    key, then maps pairs of bits to four (A_2)-inspired points.
-   After the LWE-style operation, the decoder chooses the nearest of
    the four defined points and reconstructs the encoded bytes. The
    experiment compares the recovered key against the original.

### Stage 4 --- Experimental symmetric encryption and release gate

-   `symmetric_engine.py` splits plaintext into blocks of up to 64
    bytes.
-   It generates a SHA-512-derived mask, XORs the mask with each
    plaintext block, and updates a chained state using the ciphertext.
-   A terminal value is checked during decryption. If the comparison
    fails, the code raises a `ValueError` and overwrites the temporary
    plaintext buffer before raising.

The release gate is a useful demonstration of **fail-closed application
behaviour**, but it is not a substitute for a standardized
authenticated-encryption scheme. Python cannot guarantee secure erasure
of every copy of sensitive data from process memory.

## Architecture and modules

  -----------------------------------------------------------------------
  File                                Responsibility
  ----------------------------------- -----------------------------------
  `math_core.py`                      Generation seed, parameter
                                      derivation, private function,
                                      stability checks, and secret-vector
                                      construction

  `quantum_rng.py`                    Qiskit Aer simulator-based bit/byte
                                      sampling and 32-byte session-key
                                      generation

  `lwe_engine.py`                     LWE-style public-component
                                      generation, encapsulation, and
                                      decapsulation

  `encoding.py`                       Reed--Solomon redundancy, bit
                                      serialization, (A_2)-inspired
                                      symbol mapping, and nearest-point
                                      decoding

  `symmetric_engine.py`               Experimental SHA-512/XOR chained
                                      encryption and terminal-value
                                      release gate

  `test_hexacrypt.py`                 Numerical experiment and validation
                                      checks

  `generate_statistics.py`            Generates exploratory performance,
                                      secret-vector distribution, and
                                      noise/reliability plots

  `test_run/cli.py`                   Guided command-line presentation
                                      layer for demo, architecture, and
                                      validation views

  `test_run/CLI_DEMO_README.md`       CLI usage notes
  -----------------------------------------------------------------------

The archive may include a nested `HexaCrypt_CodeV2_CLI_Demo.zip` and
duplicate files under `test_run/`. Use one consistent copy of the
modules when running an experiment; do not mix files from different
revisions.

## What the prototype has demonstrated

The repository includes scripts for these checks:

-   **Function stability:** evaluates whether the generated private
    function is monotonic over the tested domain.
-   **End-to-end key-recovery experiment:** runs repeated LWE-style
    encapsulation/decapsulation trials and measures exact session-key
    recovery.
-   **Encryption/decryption round trip:** verifies that the experimental
    symmetric engine returns the original sample plaintext when the
    terminal value is unchanged.
-   **Tamper checks:** alters ciphertext or the terminal value and
    checks that decryption fails rather than returning plaintext.
-   **Generation rotation:** derives a new generation from the same
    long-term secret and checks that the resulting secret vectors
    differ.
-   **Exploratory statistics:** scripts are provided to plot execution
    times, secret-vector values, and recovery success under selected
    injected-noise levels.

**Important:** These are code-level and empirical prototype checks, not
an independent security audit. Exact key-recovery rates depend on the
run, randomness, parameters, and implementation. The included plots are
experiment outputs, not universal performance or security guarantees.
Run the scripts yourself to obtain results for your environment.

> [Video Demonstration](https://youtu.be/qrE9RFlS_Os)

## Quick start

### 1. Requirements

-   Python 3.10 or newer is a reasonable starting point; use a virtual
    environment.
-   The project imports these packages: `numpy`, `cryptography`,
    `galois`, `qiskit`, `qiskit-aer`, `matplotlib`, and `seaborn`.
-   `matplotlib` and `seaborn` are needed for statistics/plot
    generation. The core validation code imports NumPy, Cryptography,
    Galois, and Qiskit/Qiskit Aer.

Package compatibility can vary by Python version. If installation fails,
use a clean virtual environment and install compatible releases of the
packages above.

### 2. Get the code

``` bash
git clone <YOUR-REPOSITORY-URL>
cd <YOUR-REPOSITORY-DIRECTORY>
```

Replace the placeholders with your actual GitHub URL and repository
directory. If you downloaded the provided ZIP instead, extract it first
and open a terminal in the extracted project directory.

### 3. Create and activate a virtual environment

**Windows (PowerShell):**

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

**macOS / Linux:**

``` bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 4. Install dependencies

``` bash
python -m pip install numpy cryptography galois qiskit qiskit-aer matplotlib seaborn
```

### 5. Run the numerical validation

From the directory containing `test_hexacrypt.py` and the core modules:

``` bash
python test_hexacrypt.py
```

This runs the main experiment, including key-recovery trials, a valid
symmetric round trip, terminal-value tampering, and generation rotation.
A run can take time because the simulator is used to generate many
individual measurement outcomes.

### 6. Run the guided CLI demonstrator

In the supplied archive, the CLI is located under `test_run/`. Change
into that directory so its imports resolve to the matching module
copies:

``` bash
cd test_run
python cli.py
```

Available views:

``` bash
python cli.py architecture
python cli.py validation
python cli.py demo
python cli.py demo --pace 0.20
```

-   `architecture` displays the pipeline overview and is intended to
    work without loading every engine dependency.
-   `validation` summarizes the validation flow.
-   `demo` runs the guided demonstration and may require all
    dependencies to be installed.
-   `--pace` changes the presentation delay, not the cryptographic
    parameters.

If your GitHub repository places `cli.py` at the root instead, run these
commands from the root. The commands above reflect the uploaded
archive's current layout.

### 7. Generate the exploratory plots

From the directory containing `generate_statistics.py` and the core
modules:

``` bash
python generate_statistics.py
```

The script writes: - `performance_profiling.png` -
`secret_vector_distribution.png` - `noise_vs_reliability.png`

These are generated experiment artefacts. They may be overwritten on a
subsequent run.

## Expected behaviour

A successful run should show the experiment stages and report whether
the recovered session key exactly matches the original. The
symmetric-engine checks should show:

-   Valid ciphertext and terminal value → original plaintext is
    returned.
-   Modified ciphertext or modified terminal value → decryption raises
    an authentication-failure `ValueError`.

The key-recovery experiment is stochastic and may report less than 100%
success. Treat failures as measurements to investigate---not as
something to hide or manually change in the output. If a script fails,
preserve the traceback, Python version, package versions, and command
used when reporting the issue.

## Limitations and security status

HexaCrypt is an **experimental research prototype**. Do not use it to
protect real documents, credentials, communications, keys, or other
sensitive information.

Known boundaries include:

1.  **No formal security proof or independent cryptographic audit.** The
    proposed construction has not been shown to meet a recognized
    security definition.
2.  **Custom symmetric construction.** The SHA-512/XOR chain must not be
    treated as equivalent to AES-GCM, ChaCha20-Poly1305, or another
    standardized AEAD. The terminal hash is part of the proposed design
    and is not, by itself, evidence of secure message authentication.
3.  **Simulator, not quantum hardware.** Qiskit Aer simulates quantum
    circuits; it does not establish access to physical quantum entropy
    or quantum advantage.
4.  **LWE parameter and distribution questions remain.** The prototype's
    finite parameter choices and sampling methods require deeper
    analysis before any security claim can be made.
5.  **Key-recovery correctness is empirical.** Tests over a limited
    number of trials cannot prove correctness for all keys, messages,
    noise samples, or environments.
6.  **Research encoding choices need further specification and review.**
    The (A_2) representation, scaling, noise model, and error-correction
    integration need systematic mathematical validation.
7.  **Fail-closed is not secure memory erasure.** Overwriting a Python
    bytearray does not guarantee that all copies of plaintext have been
    removed from memory.

For applications that need real security today, use established,
reviewed cryptographic libraries and standardized algorithms. HexaCrypt
should be used for learning, controlled experiments, and research
discussion only.

## Potential applications

If the design is further specified, analysed, and validated, the
research themes explored here may be relevant to:

-   Cryptography education and interactive demonstrations of
    lattice-based ideas.
-   Experiments in noisy key transport, redundancy, and decoding
    reliability.
-   Research into generation-specific secret derivation and key-rotation
    workflows.
-   Demonstrations of integrity-checking and fail-closed
    plaintext-release policies.
-   Comparative studies of simulated quantum sampling and classical
    randomness sources.

These are **potential research directions**, not validated deployment
use cases.

## Roadmap

1.  **Reproducibility:** define a pinned dependency file, supported
    Python versions, deterministic test fixtures where appropriate, and
    clear test output.
2.  **Mathematical specification:** precisely define encodings,
    parameter constraints, sampling distributions, scaling, and decoding
    rules.
3.  **Statistical evaluation:** expand key-recovery trials and noise
    sweeps; publish sample sizes, success rates, confidence intervals,
    and failure cases.
4.  **Independent review:** obtain cryptographic analysis of the
    LWE-style construction, secret distribution, (A_2) encoding, and
    symmetric layer.
5.  **Replace custom data protection:** for any future practical
    application, use a standardized KEM and AEAD selected and
    implemented through vetted cryptographic libraries.
6.  **Improved developer experience:** add automated tests, continuous
    integration, a pinned requirements file, and clearer separation
    between the research model and presentation CLI.

## Repository structure

The uploaded archive currently resembles:

``` text
Code-V2/
├── encoding.py
├── generate_statistics.py
├── lwe_engine.py
├── math_core.py
├── quantum_rng.py
├── symmetric_engine.py
├── test_hexacrypt.py
├── noise_vs_reliability.png
├── performance_profiling.png
├── secret_vector_distribution.png
├── HexaCrypt_CodeV2_CLI_Demo.zip
└── test_run/
    ├── cli.py
    ├── CLI_DEMO_README.md
    └── copies of the core modules and experiment scripts
```

The exact layout may change as the repository is cleaned up. The main
numerical test and the CLI should each be run alongside the module
copies they are intended to import.

## Contributing and responsible use

Contributions that improve reproducibility, documentation, tests,
mathematical precision, or independent analysis are welcome. Please:

-   Distinguish measured results from assumptions and hypotheses.
-   Include commands and environment details for reproduced findings.
-   Report decoding failures and edge cases rather than suppressing
    them.
-   Avoid claiming "quantum-secure," "post-quantum secure,"
    "unbreakable," or "production-ready" without an appropriate,
    independently supported basis.

## Project status

**Status:** Experimental prototype / research demonstrator\
**Primary language:** Python\
**Quantum component:** Qiskit Aer simulator\
**Security posture:** Not audited; not suitable for real-world data
protection

------------------------------------------------------------------------

HexaCrypt is a work in progress. The most useful next step is to run the
included experiments, inspect the assumptions in the source, and help
establish which parts are mathematically sound, reproducible, and worth
further research.
