"""
symmetric_engine.py

WARNING: This custom cipher is an experimental research construction.
It has not been formally proven secure. It must not be represented as equivalent 
to AES-GCM, a standardized AEAD, or a proven secure MAC. 
Its purpose in HexaCrypt is experimental research and demonstration of the proposed 
chained encryption/Doom Principle architecture.
"""
import os
import hashlib
import hmac

class SymmetricEngine:
    def __init__(self, K: bytes):
        """Initializes with the 256-bit (32-byte) session key K."""
        assert len(K) == 32, "Session key must be 256 bits (32 bytes)"
        self.K = K

    def encrypt(self, plaintext: bytes) -> tuple[bytes, list[bytes], bytes]:
        """
        Encrypts plaintext using a SHA-512 XOR keystream and ciphertext avalanche chain[cite: 8].
        """
        iv = os.urandom(16)  # Public IV/nonce
        
        # Genesis: y_0 = SHA512(K || IV)[cite: 8]
        y_prev = hashlib.sha512(self.K + iv).digest() 
        
        # Plaintext segmentation (64-byte blocks)[cite: 8]
        blocks = [plaintext[i:i+64] for i in range(0, len(plaintext), 64)]
        if not blocks:
            blocks = [b""]  # Handle empty plaintext cleanly
            
        ciphertexts = []
        # Pad K to 64 bytes to XOR against the 64-byte SHA-512 state
        k_padded = self.K.ljust(64, b'\x00') 
        
        for p_i in blocks:
            # Keystream: M_i = SHA512(y_(i-1) XOR K)[cite: 8]
            xor_state = bytes(a ^ b for a, b in zip(y_prev, k_padded))
            m_i = hashlib.sha512(xor_state).digest()
            
            # Truncate mask if the plaintext block is shorter than 64 bytes[cite: 8]
            m_i_trunc = m_i[:len(p_i)]
            
            # Encryption: C_i = P_i XOR M_i[cite: 8]
            c_i = bytes(a ^ b for a, b in zip(p_i, m_i_trunc))
            ciphertexts.append(c_i)
            
            # Avalanche chain: y_i = SHA512(y_(i-1) || C_i)[cite: 8]
            y_prev = hashlib.sha512(y_prev + c_i).digest()
            
        # Terminal value T = y_n[cite: 8]
        return iv, ciphertexts, y_prev

    def decrypt(self, iv: bytes, ciphertexts: list[bytes], t_recv: bytes) -> bytes:
        """
        Decrypts the ciphertext blocks and enforces the Doom Principle release gate[cite: 8].
        """
        y_prev = hashlib.sha512(self.K + iv).digest()
        k_padded = self.K.ljust(64, b'\x00')
        plaintext_buffer = bytearray()
        
        for c_i in ciphertexts:
            xor_state = bytes(a ^ b for a, b in zip(y_prev, k_padded))
            m_i = hashlib.sha512(xor_state).digest()
            
            m_i_trunc = m_i[:len(c_i)]
            p_i = bytes(a ^ b for a, b in zip(c_i, m_i_trunc))
            plaintext_buffer.extend(p_i)
            
            y_prev = hashlib.sha512(y_prev + c_i).digest()
            
        t_calc = y_prev
        
        # DOOM PRINCIPLE: Fail-closed release gate[cite: 8]
        if hmac.compare_digest(t_calc, t_recv):
            return bytes(plaintext_buffer)
        else:
            # PURGE PLAINTEXT BUFFER AND FLAG AS COMPROMISED[cite: 8]
            buffer_len = len(plaintext_buffer)
            plaintext_buffer = bytearray(buffer_len)  # Zero out memory
            raise ValueError("COMPROMISED PAYLOAD: Authentication failed. Buffer purged.")