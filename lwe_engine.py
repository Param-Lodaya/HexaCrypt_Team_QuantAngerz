"""
lwe_engine.py

LWE layer for key transport.
- key generation
- encapsulation
- decapsulation
"""
import numpy as np

class LWEEngine:
    def __init__(self, q: int, n: int, m: int):
        self.q = q
        self.n = n
        self.m = m

    def generate_keys(self, s_t: np.ndarray, A: np.ndarray = None, e_t: np.ndarray = None):
        """
        PK_t = (A, b_t, q)
        b_t = (A * s_t + e_t) mod q
        s_t is passed from Alice's math generation.
        A is m x n
        """
        if A is None:
            A = np.random.randint(0, self.q, size=(self.m, self.n), dtype=np.int64)
        
        if e_t is None:
            # Simple error sampling (prototype, usually discrete Gaussian)
            e_t = np.random.randint(-1, 2, size=self.m, dtype=np.int64)
            
        b_t = (A.dot(s_t) + e_t) % self.q
        
        self.PK_t = (A, b_t, self.q)
        self.s_t = s_t
        self.e_t = e_t
        return self.PK_t

    def encapsulate(self, PK_t, message_scaled: np.ndarray, r: np.ndarray = None, e1: np.ndarray = None, e2: np.ndarray = None):
        """
        message_scaled: Delta * K_hex
        u = (A^T r + e_1) mod q
        v = (b_t^T r + e_2 + message_scaled) mod q
        For a message of length l, we encrypt coordinate by coordinate.
        l = len(message_scaled)
        r is m x l
        e1 is n x l
        e2 is 1 x l
        """
        A, b_t, q = PK_t
        l = len(message_scaled)
        
        if r is None:
            r = np.random.randint(0, 2, size=(self.m, l), dtype=np.int64)
            
        if e1 is None:
            e1 = np.random.randint(-1, 2, size=(self.n, l), dtype=np.int64)
            
        if e2 is None:
            e2 = np.random.randint(-1, 2, size=(l,), dtype=np.int64)
            
        # u = (A^T * r + e1) mod q
        u = (A.T.dot(r) + e1) % q
        
        # v = (b_t^T * r + e2 + message_scaled) mod q
        v = (b_t.T.dot(r) + e2 + message_scaled) % q
        
        return u, v, r, e1, e2

    def decapsulate(self, s_t: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        """
        Z = (v - s_t^T u) mod q
        """
        Z = (v - s_t.T.dot(u)) % self.q
        
        # We need to map Z back to signed representation if q is used as [-q/2, q/2)
        # because the message might be negative (e.g. mapped A2 coordinates).
        Z_signed = np.where(Z > self.q // 2, Z - self.q, Z)
        return Z_signed
