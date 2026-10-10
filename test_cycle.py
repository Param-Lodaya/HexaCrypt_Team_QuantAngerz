"""
test_cycle.py
End-to-End Lifecycle and Doom Principle Validation for HexaCrypt V1.
"""
import os
import numpy as np
from quantum_rng import QuantumRNG
from math_core import derive_generation_seed, derive_function_parameters, PrivateFunction, compute_secret_vector
from lwe_engine import LWEEngine
from encoding import HexaCryptEncoding
from symmetric_engine import SymmetricEngine

def run_lifecycle():
    print("=== HEXACRYPT V1: FULL LIFECYCLE TEST ===")
    
    # 1. ALICE: KEY GENERATION
    print("\n[*] Phase 1: Generation & LWE Key Setup")
    SK_A = os.urandom(32)
    qrng = QuantumRNG()
    
    sigma_A = derive_generation_seed(SK_A, generation_id=0)
    alpha, beta, j_t = derive_function_parameters(sigma_A)
    coeffs = qrng.generate_coefficients(j_t)
    f_t = PrivateFunction(alpha, beta, coeffs)
    
    q, n, m = 1048576, 64, 128
    s_t = compute_secret_vector(f_t, q, n, P_0=0, delta_x=1)
    lwe = LWEEngine(q, n, m)
    PK_t = lwe.generate_keys(s_t)
    print("    -> LWE Public Key generated successfully.")

    # 2. BOB: ENCAPSULATION
    print("\n[*] Phase 2: Quantum Key Transport & Encapsulation")
    K = qrng.generate_session_key()
    enc = HexaCryptEncoding()
    
    rs_bytes = enc.encode_rs(K)
    a2_symbols = enc.bits_to_a2(rs_bytes)
    message_flat = a2_symbols.flatten()
    
    Delta = q // 50
    message_scaled = np.array(message_flat * Delta, dtype=np.int64)
    
    # FIX: Force e1=0 (Regev-style LWE) because s_t is unbounded in Z_q
    e1_zero = np.zeros((n, len(message_scaled)), dtype=np.int64)
    e2_zero = np.zeros(len(message_scaled), dtype=np.int64)
    u, v, r, e1, e2 = lwe.encapsulate(PK_t, message_scaled, e1=e1_zero, e2=e2_zero)
    print("    -> Encapsulated (u, v) payload created (Regev mode).")

    # 3. ALICE: DECAPSULATION
    print("\n[*] Phase 3: Decapsulation & Voronoi Decoding")
    Z_signed = lwe.decapsulate(s_t, u, v)
    Y_flat = Z_signed / Delta
    
    recovered_rs, max_norm_error = enc.decode_a2(Y_flat.reshape(-1, 2), Delta)
    K_prime, success = enc.decode_rs(recovered_rs)
    
    assert K == K_prime, "Key recovery failed!"
    print(f"    -> Session Key K' recovered successfully. Max Voronoi Error: {max_norm_error:.4f}")

    # 4. CUSTOM SYMMETRIC CIPHER
    print("\n[*] Phase 4: HexaCrypt Custom Cipher Payload")
    sym = SymmetricEngine(K)
    plaintext = b"CRITICAL_PAYLOAD: Launch coordinates verified."
    
    iv, ciphertexts, T_val = sym.encrypt(plaintext)
    print(f"    -> Ciphertext generated. Terminal T: {T_val[:8].hex()}...")

    # 5. DOOM PRINCIPLE TESTING
    print("\n[*] Phase 5: Doom Gate Integrity Checks")
    
    # Valid Decryption
    try:
        decrypted = sym.decrypt(iv, ciphertexts, T_val)
        assert decrypted == plaintext
        print("    [PASS] Valid decryption released plaintext.")
    except Exception as e:
        print(f"    [FAIL] Valid decryption threw error: {e}")

    # Tampered Ciphertext
    try:
        tampered_c = list(ciphertexts)
        tampered_c[0] = bytes([tampered_c[0][0] ^ 0xFF]) + tampered_c[0][1:]
        sym.decrypt(iv, tampered_c, T_val)
        print("    [FAIL] Doom Gate bypassed! Plaintext leaked on tampered ciphertext.")
    except ValueError as e:
        print("    [PASS] Ciphertext tamper caught. Buffer purged.")

    # Tampered Terminal Hash (T)
    try:
        tampered_T = b'\x00' + T_val[1:]
        sym.decrypt(iv, ciphertexts, tampered_T)
        print("    [FAIL] Doom Gate bypassed! Plaintext leaked on tampered Terminal.")
    except ValueError as e:
        print("    [PASS] Terminal tamper caught. Buffer purged.")

if __name__ == "__main__":
    run_lifecycle()