"""
encoding.py
Serialization rules:
- Byte order: Big-endian
- Bit order: MSB-first
- A2 symbol order: sequential 2-bit groups
- Coordinate order: (x, y)
- LWE message order: x0, y0, x1, y1, ..., x159, y159
"""
import galois
import numpy as np

class HexaCryptEncoding:
    def __init__(self):
        # RS(40, 32) over GF(256) is shortened from RS(255, 247).
        # We encode 247 symbols where the first 215 symbols are 0.
        self.rs = galois.ReedSolomon(255, 247)
        self.pad_len = 247 - 32
        
    def encode_rs(self, data: bytes) -> bytes:
        """Encode 32 bytes to 40 bytes."""
        assert len(data) == 32, f"Expected 32 bytes, got {len(data)}"
        padded_data = [0] * self.pad_len + list(data)
        data_gf = self.rs.field(padded_data)
        encoded = self.rs.encode(data_gf)
        # Discard the padding
        return bytes(encoded[self.pad_len:])
        
    def decode_rs(self, data: bytes) -> tuple[bytes, bool]:
        """
        Decode 40 bytes to 32 bytes.
        Returns (decoded_bytes, success)
        """
        assert len(data) == 40, f"Expected 40 bytes, got {len(data)}"
        padded_codeword = [0] * self.pad_len + list(data)
        data_gf = self.rs.field(padded_codeword)
        try:
            decoded = self.rs.decode(data_gf)
            return bytes(decoded[self.pad_len:]), True
        except galois.ReedSolomonError:
            # Decoding failed
            return bytes(32), False

    def bits_to_a2(self, rs_bytes: bytes) -> np.ndarray:
        """
        Map 40 bytes to 160 A2 symbols.
        Each symbol is a 2D coordinate.
        Returns array of shape (160, 2)
        
        00 -> (0,0)
        01 -> (1,0)
        10 -> (1/2, sqrt(3)/2)
        11 -> (-1/2, sqrt(3)/2)
        """
        mapping = {
            '00': (0.0, 0.0),
            '01': (1.0, 0.0),
            '10': (0.5, np.sqrt(3)/2),
            '11': (-0.5, np.sqrt(3)/2)
        }
        
        # Interpret each byte as 8 bits, MSB first
        bits = "".join([f"{b:08b}" for b in rs_bytes])
        assert len(bits) == 320
        
        symbols = []
        for i in range(0, 320, 2):
            pair = bits[i:i+2]
            symbols.append(mapping[pair])
            
        return np.array(symbols)

    def decode_a2(self, y_k: np.ndarray, delta: int) -> tuple[bytes, float]:
        """
        Applies Voronoi nearest-point decoding. 
        Returns decoded bytes and the maximum calculated normalized error ||E_eff / Delta||.
        """
        valid_points = [
            ((0.0, 0.0), '00'),
            ((1.0, 0.0), '01'),
            ((0.5, np.sqrt(3)/2), '10'),
            ((-0.5, np.sqrt(3)/2), '11')
        ]
        
        bits = ""
        max_norm_error = 0.0
        
        for pt in y_k:
            best_dist = float('inf')
            best_pair = '00'
            for v_pt, pair in valid_points:
                # Euclidean distance squared
                dist_sq = (pt[0] - v_pt[0])**2 + (pt[1] - v_pt[1])**2 
                if dist_sq < best_dist:
                    best_dist = dist_sq
                    best_pair = pair
            
            # Sufficient Voronoi condition: ||n|| = sqrt(best_dist)
            norm_error = np.sqrt(best_dist)
            if norm_error > max_norm_error:
                max_norm_error = norm_error
                
            bits += best_pair
            
        assert len(bits) == 320
        
        # Bits to bytes (MSB-first, Big-endian)
        res_bytes = bytearray()
        for i in range(0, 320, 8):
            byte_str = bits[i:i+8]
            res_bytes.append(int(byte_str, 2))
            
        return bytes(res_bytes), max_norm_error