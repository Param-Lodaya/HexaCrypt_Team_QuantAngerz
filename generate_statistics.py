"""
generate_statistics.py
Generates empirical data and plots for the patched HexaCrypt V1.
"""
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from quantum_rng import QuantumRNG
from math_core import derive_generation_seed, derive_function_parameters, PrivateFunction, compute_secret_vector
from lwe_engine import LWEEngine
from encoding import HexaCryptEncoding

sns.set_theme(style="whitegrid")

def generate_performance_chart():
    print("[*] Profiling Performance...")
    qrng = QuantumRNG()
    q, n, m = 1048576, 64, 128
    
    # Gen
    t0 = time.time()
    SK_A = os.urandom(32)
    sigma_A = derive_generation_seed(SK_A, 0)
    alpha, beta, j = derive_function_parameters(sigma_A)
    coeffs = qrng.generate_coefficients(j)
    f_t = PrivateFunction(alpha, beta, coeffs)
    s_t = compute_secret_vector(f_t, q, n, P_0=0, delta_x=1)
    lwe = LWEEngine(q, n, m)
    PK_t = lwe.generate_keys(s_t)
    t_gen = time.time() - t0
    
    # Encaps
    t0 = time.time()
    K = qrng.generate_session_key()
    enc = HexaCryptEncoding()
    rs_bytes = enc.encode_rs(K)
    message_flat = enc.bits_to_a2(rs_bytes).flatten()
    Delta = q // 50
    message_scaled = np.array(message_flat * Delta, dtype=np.int64)
    u, v, r, e1, e2 = lwe.encapsulate(PK_t, message_scaled)
    t_enc = time.time() - t0
    
    # Decaps
    t0 = time.time()
    Z_signed = lwe.decapsulate(s_t, u, v)
    Y_flat = Z_signed / Delta
    recovered_rs, _ = enc.decode_a2(Y_flat.reshape(-1, 2), Delta)
    K_p, _ = enc.decode_rs(recovered_rs)
    t_dec = time.time() - t0
    
    labels = ['Gen 0 Setup', 'Bob Encaps', 'Alice Decaps (Voronoi)']
    times = [t_gen, t_enc, t_dec]
    
    plt.figure(figsize=(8, 5))
    sns.barplot(x=labels, y=times, hue=labels, palette="magma", legend=False)
    plt.title("HexaCrypt V1: Subsystem Execution Time", fontsize=14)
    plt.ylabel("Time (seconds)", fontsize=12)
    plt.savefig("performance_profiling.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("    -> Saved performance_profiling.png")
    
    return s_t, PK_t, lwe, enc, q, n, m, Delta

def generate_secret_vector_histogram(s_t):
    print("[*] Generating Secret Vector Distribution...")
    plt.figure(figsize=(8, 5))
    sns.histplot(s_t, bins=30, kde=True, color="indigo")
    plt.title("Empirical Secret Vector ($s_t$) Distribution Modulo q", fontsize=14)
    plt.xlabel("Value Domain ($Z_q$)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.savefig("secret_vector_distribution.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("    -> Saved secret_vector_distribution.png")

def generate_noise_vs_reliability(s_t, lwe, enc, Delta, n, m):
    print("[*] Simulating full E_eff noise impact...")
    qrng = QuantumRNG()
    K = qrng.generate_session_key()
    rs_bytes = enc.encode_rs(K)
    message_flat = enc.bits_to_a2(rs_bytes).flatten()
    message_scaled = np.array(message_flat * Delta, dtype=np.int64)
    
    # Sweeping standard deviations for the noise distributions
    noise_stds = [0, 10, 50, 100, 200, 300, 500, 800, 1000]
    success_rates = []
    trials_per_level = 20
    
    for std in noise_stds:
        successes = 0
        for _ in range(trials_per_level):
            # Injecting comprehensive noise across e_t, e1, and e2
            e_t = np.random.normal(0, std, size=m).astype(np.int64)
            e1 = np.zeros((n, len(message_scaled)), dtype=np.int64)
            e2 = np.random.normal(0, std, size=len(message_scaled)).astype(np.int64)
            
            PK_t_noisy = lwe.generate_keys(s_t, e_t=e_t)
            u, v, r, e1_ret, e2_ret = lwe.encapsulate(PK_t_noisy, message_scaled, e1=e1, e2=e2)
            Z_signed = lwe.decapsulate(s_t, u, v)
            
            Y_flat = Z_signed / Delta
            recovered_rs, _ = enc.decode_a2(Y_flat.reshape(-1, 2), Delta)
            K_p, _ = enc.decode_rs(recovered_rs)
            if K == K_p:
                successes += 1
                
        success_rates.append(successes / trials_per_level)
        print(f"    Noise STD {std}: P(K'=K) = {success_rates[-1]:.2f}")
        
    plt.figure(figsize=(8, 5))
    plt.plot(noise_stds, success_rates, marker='o', linestyle='-', color="crimson", linewidth=2)
    plt.title("Decoding Reliability vs. Injected Gaussian Noise", fontsize=14)
    plt.xlabel("Noise Standard Deviation ($\\sigma$)", fontsize=12)
    plt.ylabel("Probability of Exact Key Recovery $P(K' = K)$", fontsize=12)
    plt.ylim(-0.05, 1.05)
    plt.grid(True, which="both", ls="--")
    plt.savefig("noise_vs_reliability.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("    -> Saved noise_vs_reliability.png")

if __name__ == "__main__":
    s_t, PK_t, lwe, enc, q, n, m, Delta = generate_performance_chart()
    generate_secret_vector_histogram(s_t)
    generate_noise_vs_reliability(s_t, lwe, enc, Delta, n, m)
    print("\n[+] All metrics successfully generated.")