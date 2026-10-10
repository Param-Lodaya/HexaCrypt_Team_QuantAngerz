"""
HexaCrypt CLI — Guided Research Demonstrator
---------------------------------------------
This file is intentionally presentation-oriented. It does not replace the
cryptographic modules; it orchestrates them into a visual, judge-friendly flow.

Run:
    python cli.py
    python cli.py demo
    python cli.py demo --pace 0.35
    python cli.py architecture
    python cli.py validation

The CLI is a visualization/orchestration layer around the existing prototype.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from dataclasses import dataclass
from typing import Callable, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Theme — ANSI only, no third-party UI dependency
# ─────────────────────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
WHITE = "\033[97m"
GRAY = "\033[90m"

WIDTH = 78


def c(text: str, colour: str = WHITE) -> str:
    return f"{colour}{text}{RESET}"


def clear():
    # Keep captured videos clean; Windows 10+ terminals generally support this.
    print("\033[2J\033[H", end="")


def rule(char="─"):
    print(c(char * WIDTH, GRAY))


def title(text: str):
    print()
    print(c("  " + text, BOLD + WHITE))
    rule()


def banner():
    print(c("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              H E X A C R Y P T                              ║
║                  Hybrid Lattice Cryptography Research Prototype             ║
║                                                                            ║
║       QUANTUM-ASSISTED ENTROPY  •  PRIVATE FUNCTION  •  LWE  •  A₂        ║
║                       •  DOOM / RELEASE GATE  •                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
""", CYAN))
    print(c("  RESEARCH PROTOTYPE  |  DEMONSTRATION BUILD  |  NOT A PRODUCTION CIPHER",
             DIM + YELLOW))
    print()


def badge(label: str, value: str, colour=GREEN):
    print(f"  {c('●', colour)} {c(label + ':', BOLD)} {value}")


def kv(label: str, value: str, colour=WHITE):
    print(f"  {c(label.ljust(22), DIM)} {c(str(value), colour)}")


def short_hex(x: bytes, n=8):
    return x[:n].hex().upper() + "…"


def fingerprint(x: bytes):
    return hashlib.sha256(x).hexdigest()[:12].upper()


def progress(label: str, steps=18, delay=0.02):
    print(f"  {c(label.ljust(34), DIM)}", end="", flush=True)
    for i in range(steps):
        print(c("█", CYAN), end="", flush=True)
        time.sleep(delay)
    print(c("  OK", GREEN))


def pause(seconds: float):
    if seconds > 0:
        time.sleep(seconds)


def phase_header(number: str, name: str, subtitle: str):
    print()
    print(c(f"  PHASE {number}  /  {name.upper()}", BOLD + CYAN))
    print(c(f"  {subtitle}", DIM))
    rule("·")


def flow_line(items):
    print("  " + c("  →  ".join(items), CYAN))


def import_engine():
    """
    Import project modules lazily so `python cli.py architecture` can work even
    when optional cryptographic/quantum dependencies are not installed.
    """
    try:
        import numpy as np
        from quantum_rng import QuantumRNG
        from math_core import (
            derive_generation_seed,
            derive_function_parameters,
            PrivateFunction,
            compute_secret_vector,
            validate_function_stability,
        )
        from lwe_engine import LWEEngine
        from encoding import HexaCryptEncoding
        from symmetric_engine import SymmetricEngine
        return {
            "np": np,
            "QuantumRNG": QuantumRNG,
            "derive_generation_seed": derive_generation_seed,
            "derive_function_parameters": derive_function_parameters,
            "PrivateFunction": PrivateFunction,
            "compute_secret_vector": compute_secret_vector,
            "validate_function_stability": validate_function_stability,
            "LWEEngine": LWEEngine,
            "HexaCryptEncoding": HexaCryptEncoding,
            "SymmetricEngine": SymmetricEngine,
        }
    except Exception as exc:
        print(c("\n  Engine dependency error:", RED + BOLD))
        print(c(f"  {type(exc).__name__}: {exc}", RED))
        print(c("\n  Install the project's requirements before running the live demo.",
                YELLOW))
        print(c("  The architecture screen is dependency-free.", DIM))
        return None


@dataclass
class DemoState:
    SK_A: bytes
    sigma_A: bytes
    alpha: float
    beta: float
    j_t: int
    coeffs: list
    f_t: object
    s_t: object
    PK_t: tuple
    K: bytes
    K_prime: bytes
    key_success: bool
    max_norm_error: float
    iv: bytes
    ciphertexts: list
    terminal: bytes
    plaintext: bytes


def architecture():
    clear()
    banner()
    title("THE HEXACRYPT STORY")
    print(c("""
  The terminal is deliberately organized as a narrative instead of a
  conventional application dashboard.

      ALICE / SECRET
            │
            ▼
      PRIVATE FUNCTION
            │
            ▼
      DISCRETE INTEGRATION → FORWARD DIFFERENCE
            │
            ▼
      SECRET VECTOR → LWE PUBLIC KEY
            │
            │                 BOB
            │                  │
            │                  ▼
            │          QUANTUM-ASSISTED KEY
            │                  │
            │                  ▼
            └──────────────► A₂ ENCODING
                               │
                               ▼
                         (u, v) TRANSPORT
                               │
                               ▼
                         VORONOI DECODING
                               │
                               ▼
                         SHARED 256-BIT K
                               │
                               ▼
                       SYMMETRIC PAYLOAD
                               │
                               ▼
                         TERMINAL VALUE T
                               │
                               ▼
                      ┌──── DOOM GATE ────┐
                      │                   │
                   MATCH               MISMATCH
                      │                   │
                   RELEASE            PURGE + FLAG
    """, WHITE))
    rule()
    print(c("  What the judges should remember:", BOLD + WHITE))
    print()
    badge("1", "The long-term secret never leaves Alice.", CYAN)
    badge("2", "Bob transports a fresh 256-bit session key through the lattice layer.", CYAN)
    badge("3", "The payload is only released if the terminal integrity value matches.", CYAN)
    print()
    print(c("  Research boundary: this is an experimental cryptographic construction.",
            DIM + YELLOW))


def build_demo(pace: float = 0.35) -> DemoState:
    E = import_engine()
    if E is None:
        raise RuntimeError("Dependencies unavailable")

    np = E["np"]
    QuantumRNG = E["QuantumRNG"]
    derive_generation_seed = E["derive_generation_seed"]
    derive_function_parameters = E["derive_function_parameters"]
    PrivateFunction = E["PrivateFunction"]
    compute_secret_vector = E["compute_secret_vector"]
    validate_function_stability = E["validate_function_stability"]
    LWEEngine = E["LWEEngine"]
    HexaCryptEncoding = E["HexaCryptEncoding"]
    SymmetricEngine = E["SymmetricEngine"]

    clear()
    banner()

    # ── Phase 0 ──────────────────────────────────────────────────────────────
    phase_header("00", "Initialize", "One payload. One session. One release decision.")
    plaintext = b"HexaCrypt experimental payload :: Q-HACK INDIA 2026"
    kv("Payload", plaintext.decode())
    kv("Payload size", f"{len(plaintext)} bytes")
    kv("Generation", "G-0001")
    kv("Security mode", "experimental / research")
    pause(pace)

    # ── Phase 1 ──────────────────────────────────────────────────────────────
    phase_header("01", "Alice locks the generation",
                 "Long-term secret → private generation state → LWE secret vector")
    SK_A = os.urandom(32)
    qrng = QuantumRNG()

    progress("Deriving private generation seed", delay=0.01)
    sigma_A = derive_generation_seed(SK_A, generation_id=0)
    alpha, beta, j_t = derive_function_parameters(sigma_A)

    progress("Generating function coefficients", delay=0.01)
    coeffs = qrng.generate_coefficients(j_t)
    f_t = PrivateFunction(alpha, beta, coeffs)

    q, n, m = 1048576, 64, 128
    stability = validate_function_stability(f_t, p_0=0, delta_x=1, n=n)

    progress("Computing locked secret vector", delay=0.01)
    s_t = compute_secret_vector(f_t, q, n, P_0=0, delta_x=1)

    progress("Building LWE public component", delay=0.01)
    lwe = LWEEngine(q, n, m)
    PK_t = lwe.generate_keys(s_t)

    kv("SK_A fingerprint", fingerprint(SK_A), CYAN)
    kv("Private seed σ_A", short_hex(sigma_A), CYAN)
    kv("Function degree", j_t)
    kv("Monotonic", stability["is_monotonic"], GREEN if stability["is_monotonic"] else RED)
    kv("Secret vector", f"s ∈ Zq^{n}  |  n={n}")
    kv("Public key", f"A={m}×{n}, b={m}, q={q}")
    print()
    flow_line(["SK_A", "σ_A", "f_A(x)", "s", "PK_A"])
    badge("BOUNDARY", "Bob receives PK_A — not SK_A, σ_A, f_A(x), or s", YELLOW)
    pause(pace)

    # ── Phase 2 ──────────────────────────────────────────────────────────────
    phase_header("02", "Bob transports a fresh session key",
                 "Quantum-assisted entropy → Reed–Solomon → A₂ symbols → LWE ciphertext")
    K = qrng.generate_session_key()
    enc = HexaCryptEncoding()

    progress("Generating 256-bit session key", delay=0.01)
    rs_bytes = enc.encode_rs(K)
    a2_symbols = enc.bits_to_a2(rs_bytes)
    message_flat = a2_symbols.flatten()

    Delta = q // 50
    message_scaled = np.array(message_flat * Delta, dtype=np.int64)

    # Preserve the upgraded prototype's Regev-mode setting used by its
    # lifecycle validation.
    e1_zero = np.zeros((n, len(message_scaled)), dtype=np.int64)
    e2_zero = np.zeros(len(message_scaled), dtype=np.int64)

    progress("Encoding key with Reed–Solomon", delay=0.01)
    progress("Mapping 320 bits into 160 A₂ symbols", delay=0.01)
    progress("Encapsulating A₂ message through LWE", delay=0.01)
    u, v, r, e1, e2 = lwe.encapsulate(
        PK_t, message_scaled, e1=e1_zero, e2=e2_zero
    )

    kv("Session key K", short_hex(K), CYAN)
    kv("Key fingerprint", fingerprint(K), CYAN)
    kv("RS protected size", "32 → 40 bytes")
    kv("A₂ representation", "160 × 2D symbols")
    kv("Ciphertext", f"u={u.shape}, v={v.shape}")
    flow_line(["K", "RS(40B)", "A₂(160)", "(u, v)"])
    pause(pace)

    # ── Phase 3 ──────────────────────────────────────────────────────────────
    phase_header("03", "Alice recovers the session key",
                 "Remove LWE component → normalize → Voronoi nearest-point decode")
    progress("Computing Z = v − sᵀu", delay=0.01)
    Z_signed = lwe.decapsulate(s_t, u, v)

    Y_flat = Z_signed / Delta

    progress("Applying A₂ Voronoi decoding", delay=0.01)
    recovered_rs, max_norm_error = enc.decode_a2(
        Y_flat.reshape(-1, 2), Delta
    )

    progress("Reconstructing 256-bit session key", delay=0.01)
    K_prime, success = enc.decode_rs(recovered_rs)

    kv("Recovered K′", short_hex(K_prime), GREEN if success else RED)
    kv("K′ == K", success and K == K_prime, GREEN if success and K == K_prime else RED)
    kv("Max normalized error", f"{max_norm_error:.6f}")
    print()
    badge("A₂ DECODER", "nearest valid lattice symbol selected for every coordinate",
          CYAN)
    pause(pace)

    # ── Phase 4 ──────────────────────────────────────────────────────────────
    phase_header("04", "Protect the payload",
                 "256-bit K → SHA-512 chain → ciphertext blocks → terminal T")
    sym = SymmetricEngine(K)
    progress("Deriving genesis state y₀", delay=0.01)
    progress("Encrypting payload blocks", delay=0.01)
    iv, ciphertexts, T_val = sym.encrypt(plaintext)

    kv("IV", short_hex(iv), CYAN)
    kv("Ciphertext blocks", len(ciphertexts))
    kv("Terminal T", short_hex(T_val), CYAN)
    flow_line(["K + IV", "y₀", "Mᵢ", "Cᵢ", "yₙ = T"])
    pause(pace)

    # ── Phase 5 ──────────────────────────────────────────────────────────────
    phase_header("05", "Doom / Release Gate",
                 "The receiver reconstructs the chain before releasing plaintext")
    print()
    print(c("  VALID PAYLOAD", BOLD + GREEN))
    progress("Reconstructing terminal value", delay=0.01)
    decrypted = sym.decrypt(iv, ciphertexts, T_val)
    valid_release = decrypted == plaintext
    badge("DECISION", "RELEASE DATA" if valid_release else "PURGE + FLAG",
          GREEN if valid_release else RED)
    if valid_release:
        print(c(f"  → {decrypted.decode()}", WHITE))
    pause(pace)

    print()
    print(c("  TAMPER TEST", BOLD + YELLOW))
    tampered = list(ciphertexts)
    tampered[0] = bytes([tampered[0][0] ^ 0xFF]) + tampered[0][1:]
    try:
        sym.decrypt(iv, tampered, T_val)
        tamper_pass = False
    except ValueError:
        tamper_pass = True
    badge("DECISION", "PURGE + FLAG" if tamper_pass else "BYPASS",
          GREEN if tamper_pass else RED)
    print(c("  → Ciphertext modification detected before release.", DIM))
    pause(pace)

    # Final scorecard
    print()
    rule()
    print(c("  DEMO RESULT", BOLD + CYAN))
    badge("KEY RECOVERY", "PASS" if success and K == K_prime else "FAIL",
          GREEN if success and K == K_prime else RED)
    badge("VALID RELEASE", "PASS" if valid_release else "FAIL",
          GREEN if valid_release else RED)
    badge("TAMPER REJECTION", "PASS" if tamper_pass else "FAIL",
          GREEN if tamper_pass else RED)
    print()
    print(c("  HEXACRYPT: secret → lattice transport → payload → release decision",
            BOLD + WHITE))
    print(c("  Experimental research prototype — not a production cryptosystem.",
            DIM + YELLOW))

    return DemoState(
        SK_A, sigma_A, alpha, beta, j_t, coeffs, f_t, s_t, PK_t,
        K, K_prime, success, max_norm_error, iv, ciphertexts, T_val, plaintext
    )


def validation():
    clear()
    banner()
    title("VALIDATION SNAPSHOT")
    print(c("""
  This screen is intentionally a summary. For the research evaluation,
  use the existing test_hexacrypt.py experiment rather than duplicating
  its entire output inside the showcase UI.
    """, DIM))
    print()
    badge("EXPERIMENT", "100 noisy LWE trials", CYAN)
    badge("PRIMARY METRIC", "P(K′ = K)", CYAN)
    badge("NOISE METRIC", "max |E_eff| / Δ", CYAN)
    badge("INTEGRITY", "valid + terminal tamper tests", CYAN)
    badge("ROTATION", "generation 0 secret ≠ generation 1 secret", CYAN)
    print()
    rule()
    print(c("  To run the complete numerical experiment:", WHITE))
    print(c("      python test_hexacrypt.py", BOLD + CYAN))
    print()
    print(c("  The showcase CLI intentionally avoids flooding the judge with raw",
            DIM))
    print(c("  statistical output.", DIM))


def main():
    parser = argparse.ArgumentParser(
        description="HexaCrypt guided terminal demonstrator"
    )
    parser.add_argument(
        "command", nargs="?", default="menu",
        choices=["menu", "demo", "architecture", "validation"]
    )
    parser.add_argument(
        "--pace", type=float, default=0.35,
        help="pause between demo scenes (seconds)"
    )
    args = parser.parse_args()

    if args.command == "architecture":
        architecture()
        return

    if args.command == "validation":
        validation()
        return

    if args.command == "demo":
        build_demo(max(0.0, args.pace))
        return

    # Menu mode
    while True:
        clear()
        banner()
        print(c("  SELECT DEMO SCENE", BOLD + WHITE))
        print()
        print(c("  [1]", CYAN), "Guided Demo       — full story, phase by phase")
        print(c("  [2]", CYAN), "Architecture      — visual system map")
        print(c("  [3]", CYAN), "Validation        — research metrics")
        print(c("  [Q]", CYAN), "Quit")
        print()
        choice = input(c("  hexacrypt> ", BOLD + CYAN)).strip().lower()

        if choice == "1":
            try:
                build_demo(0.35)
            except RuntimeError:
                pass
            input(c("\n  Press Enter to return to menu...", DIM))
        elif choice == "2":
            architecture()
            input(c("\n  Press Enter to return to menu...", DIM))
        elif choice == "3":
            validation()
            input(c("\n  Press Enter to return to menu...", DIM))
        elif choice == "q":
            print(c("\n  Session closed. Keep the mathematics; keep the story simple.\n",
                    CYAN))
            break


if __name__ == "__main__":
    main()
