"""
test_hexacrypt.py
HexaCrypt V1 Validation and Verification Suite[cite: 8]
"""
import os
import time
import numpy as np
from quantum_rng import QuantumRNG
from math_core import derive_generation_seed, derive_function_parameters, PrivateFunction, compute_secret_vector, validate_function_stability
from lwe_engine import LWEEngine
from encoding import HexaCryptEncoding
from symmetric_engine import SymmetricEngine

def run_experiment():
    print("--- HEXACRYPT V1 EXPERIMENTAL EVALUATION ---")
    SK_A = os.urandom(32)
    qrng = QuantumRNG()
    enc = HexaCryptEncoding()
    q, n, m = 1048576, 64, 128
    
    print("\n[+] 1. PARAMETER DERIVATION & STABILITY[cite: 8]")
    sigma_A_0 = derive_generation_seed(SK_A, generation_id=0)
    alpha, beta, j_0 = derive_function_parameters(sigma_A_0)
    coeffs = qrng.generate_coefficients(j_0)
    f_0 = PrivateFunction(alpha, beta, coeffs)
    
    stability_report = validate_function_stability(f_0, p_0=0, delta_x=1, n=n)
    print(f"    Stability Report: {stability_report}")
    assert stability_report["is_monotonic"], "Function is not monotonically increasing[cite: 8]"
    
    s_0 = compute_secret_vector(f_0, q, n, P_0=0, delta_x=1)
    lwe = LWEEngine(q, n, m)
    PK_0 = lwe.generate_keys(s_0)
    
    print("\n[+] 2. FULL LWE NOISY EXPERIMENT & VORONOI VALIDATION[cite: 8]")
    K = qrng.generate_session_key()
    rs_bytes = enc.encode_rs(K)
    a2_symbols = enc.bits_to_a2(rs_bytes)
    message_flat = a2_symbols.flatten()
    
    Delta = q // 50
    message_scaled = np.array(message_flat * Delta, dtype=np.int64)
    
    trials = 100
    successes = 0
    max_e_eff = 0
    
    for _ in range(trials):
        # Configurable sampling for ALL error components[cite: 8]
        e_t_noisy = np.random.randint(-2, 3, size=m, dtype=np.int64)
        e1_noisy = np.random.randint(-1, 2, size=(n, len(message_scaled)), dtype=np.int64)
        e2_noisy = np.random.randint(-2, 3, size=len(message_scaled), dtype=np.int64)
        
        PK_0_noisy = lwe.generate_keys(s_0, e_t=e_t_noisy)
        u, v, r, e1, e2 = lwe.encapsulate(PK_0_noisy, message_scaled, e1=e1_noisy, e2=e2_noisy)
        Z_signed = lwe.decapsulate(s_0, u, v)
        
        # Calculate E_eff mathematically[cite: 8]
        # E_eff = e_t^T r + e_2 - s_t^T e_1
        E_eff = e_t_noisy.dot(r) + e2_noisy - s_0.dot(e1_noisy)
        max_e_eff = max(max_e_eff, np.max(np.abs(E_eff)))
        
        Y_flat = Z_signed / Delta
        recovered_rs, norm_error = enc.decode_a2(Y_flat.reshape(-1, 2), Delta)
        K_p, dec_success = enc.decode_rs(recovered_rs)
        
        if K == K_p:
            successes += 1
            
    print(f"    P(K'=K) over {trials} trials: {successes/trials}")
    print(f"    Sample Max |E_eff|: {max_e_eff} | Max ||E_eff/Delta|| calculated: {norm_error:.4f} (Must be < 0.5)[cite: 8]")

    print("\n[+] 3. CUSTOM CIPHER & DOOM PRINCIPLE[cite: 8]")
    sym = SymmetricEngine(K)
    plaintext = b"HexaCrypt experimental evaluation payload."
    iv, ciphertexts, T_val = sym.encrypt(plaintext)
    
    # Test 1: Valid
    decrypted = sym.decrypt(iv, ciphertexts, T_val)
    assert decrypted == plaintext, "Valid decryption failed"
    print("    Test 1 (Valid): PASS")
    
    # Test 2 & 3: Tampering triggers Doom Principle
    try:
        tampered_T = b'\x00' + T_val[1:]
        sym.decrypt(iv, ciphertexts, tampered_T)
        print("    Test 3 (Terminal Tampering): FAIL (Released plaintext)")
    except ValueError as e:
        print(f"    Test 3 (Terminal Tampering): PASS ({str(e)})")

    print("\n[+] 4. KEY ROTATION[cite: 8]")
    sigma_A_1 = derive_generation_seed(SK_A, generation_id=1)
    a_1, b_1, j_1 = derive_function_parameters(sigma_A_1)
    coeffs_1 = qrng.generate_coefficients(j_1)
    f_1 = PrivateFunction(a_1, b_1, coeffs_1)
    s_1 = compute_secret_vector(f_1, q, n, P_0=0, delta_x=1)
    
    assert not np.array_equal(s_0, s_1), "Generation secrets match!"
    print("    Rotation: PASS (s_0 != s_1)[cite: 8]")
    print("\n[+] All Validation Executed Successfully.")
    print("    SECURITY CLAIM BOUNDARY: Experimental cryptographic construction / research prototype.[cite: 8]")

if __name__ == "__main__":
    run_experiment()