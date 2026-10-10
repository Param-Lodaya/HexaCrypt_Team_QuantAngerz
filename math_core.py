"""
math_core.py
"""
import numpy as np
import hashlib
from decimal import Decimal, getcontext
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

# Prevent IEEE 754 floating-point precision collapse for massive exponentials
getcontext().prec = 100

# Configuration parameter for bounding the function domain safely[cite: 8]
X_MAX = 70.0  

def derive_generation_seed(SK_A: bytes, generation_id: int) -> bytes:
    """Generation KDF: Binds the long-term secret and generation ID deterministically[cite: 8]."""
    info = b"HexaCrypt-F|generation|" + str(generation_id).encode()
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info)
    return hkdf.derive(SK_A)

def derive_function_parameters(sigma_A_t: bytes, j_min: int = 4, j_max: int = 16):
    """Derive deterministic parameters from generation seed using explicit labels[cite: 8]."""
    h1 = hashlib.sha256(sigma_A_t + b"alpha").digest()
    h2 = hashlib.sha256(sigma_A_t + b"beta").digest()
    h3 = hashlib.sha256(sigma_A_t + b"degree").digest()
    
    alpha = float(h1[0] + 1)
    beta = float(h2[0] + 1)
    j_t = j_min + (h3[0] % (j_max - j_min + 1))
    
    return alpha, beta, j_t

class PrivateFunction:
    def __init__(self, alpha: float, beta: float, coeffs: list[int]):
        # Convert all parameters to high-precision Decimals
        self.alpha = Decimal(str(alpha))
        self.beta = Decimal(str(beta))
        self.coeffs = [Decimal(str(c)) for c in coeffs]
        
    def eval(self, x: float) -> Decimal:
        """Evaluate f_t(x) with arbitrary precision to prevent bit-loss[cite: 8]."""
        if not (0 <= x <= X_MAX):
            raise ValueError(f"Domain error: x={x} is outside [0, {X_MAX}][cite: 8]")
            
        dec_x = Decimal(str(x))
        
        # Avoid Decimal('0') ** 0 which raises InvalidOperation
        p_x = Decimal('0')
        for i, c in enumerate(self.coeffs):
            if i == 0:
                p_x += c  # x^0 is mathematically 1, so we just add the coefficient
            else:
                p_x += c * (dec_x ** i)
        
        val = self.alpha * dec_x.exp() + self.beta * p_x
        return val
        
    def derivative_eval(self, x: float) -> Decimal:
        if not (0 <= x <= X_MAX):
            raise ValueError(f"Domain error: x={x} is outside [0, {X_MAX}]")
            
        dec_x = Decimal(str(x))
        
        # Avoid 0 ** 0 when i = 1 (since i - 1 = 0)
        p_prime_x = Decimal('0')
        for i, c in enumerate(self.coeffs):
            if i > 0:
                if i == 1:
                    p_prime_x += Decimal(str(i)) * c
                else:
                    p_prime_x += Decimal(str(i)) * c * (dec_x ** (i - 1))
                    
        return self.alpha * dec_x.exp() + self.beta * p_prime_x

def validate_function_stability(f_t: PrivateFunction, p_0: int, delta_x: int, n: int) -> dict:
    """Samples the valid domain to verify finite bounds and monotonicity (f_t'(x) > 0)[cite: 8]."""
    x_max_required = p_0 + (n * delta_x)
    assert x_max_required <= X_MAX, "Required domain exceeds X_MAX"
    
    derivs = []
    monotonic = True
    overflow = False
    
    try:
        for x in np.linspace(0, x_max_required, 1000):
            # Convert Decimal back to float solely for the max/min dictionary report
            d_val = float(f_t.derivative_eval(float(x)))
            derivs.append(d_val)
            if d_val <= 0:
                monotonic = False
    except OverflowError:
        overflow = True
        
    return {
        "min_derivative": min(derivs) if derivs else None,
        "max_derivative": max(derivs) if derivs else None,
        "is_monotonic": monotonic,
        "overflow_occurred": overflow
    }

def compute_secret_vector(f_t: PrivateFunction, q: int, n: int, P_0: int, delta_x: int) -> np.ndarray:
    """Discrete integration and forward difference modular reduction[cite: 8]."""
    integrals = []
    for i in range(n + 1):
        P_i = P_0 + i * delta_x
        Q_i = P_i + delta_x
        I_i = sum(f_t.eval(float(x)) for x in range(P_i, Q_i))
        integrals.append(I_i)
        
    s_t = []
    
    # Calculate the deterministic C multiplier in high precision
    j_t = len(f_t.coeffs) - 1
    C = f_t.alpha * f_t.beta * Decimal(str(j_t)) * Decimal('100000.0')
    
    for i in range(n):
        P_i = P_0 + i * delta_x
        Q_i = P_i + delta_x
        
        D_i_plus_I = integrals[i+1] - integrals[i]
        
        # Apply the vertical scalar C before rounding and modulo[cite: 8]
        # Decimal type perfectly preserves all lower integer bits during evaluation.
        val = (f_t.eval(float(Q_i)) - D_i_plus_I) * C
        
        # Explicit deterministic rounding mathematically wraps around Z_q[cite: 8]
        val_int = int(round(val))
        s_t.append(val_int % q)
        
    return np.array(s_t, dtype=np.int64)