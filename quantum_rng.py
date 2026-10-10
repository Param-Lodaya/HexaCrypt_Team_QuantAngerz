"""
quantum_rng.py

Quantum-assisted randomness generation using Qiskit.
Provides 1-qubit coefficient generation and 8-qubit byte generation.
"""
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

class QuantumRNG:
    def __init__(self):
        # We use a simulator as specified by the "quantum-assisted" prototype nature
        self.simulator = AerSimulator()

    def generate_quantum_bit(self) -> int:
        """
        Generate a single bit {0,1} using a 1-qubit circuit with a Hadamard gate.
        |0> -> H -> Measure
        """
        qc = QuantumCircuit(1, 1)
        qc.h(0)
        qc.measure(0, 0)
        
        compiled_circuit = transpile(qc, self.simulator)
        result = self.simulator.run(compiled_circuit, shots=1).result()
        counts = result.get_counts(compiled_circuit)
        
        # Returns '0' or '1'
        bit_str = list(counts.keys())[0]
        return int(bit_str)

    def generate_coefficients(self, j_t: int) -> list[int]:
        """
        Generates j_t + 1 coefficients for a polynomial of degree j_t.
        Each coefficient is generated independently via a 1-qubit circuit.
        Returns: [c_0, c_1, ..., c_{j_t}]
        """
        return [self.generate_quantum_bit() for _ in range(j_t + 1)]

    def generate_quantum_byte(self) -> int:
        """
        Generate a single 8-bit byte using an 8-qubit circuit with Hadamard gates.
        """
        qc = QuantumCircuit(8, 8)
        for i in range(8):
            qc.h(i)
            qc.measure(i, i)
            
        compiled_circuit = transpile(qc, self.simulator)
        result = self.simulator.run(compiled_circuit, shots=1).result()
        counts = result.get_counts(compiled_circuit)
        
        # Result is an 8-character string of 0s and 1s, e.g., '10110010'
        bit_str = list(counts.keys())[0]
        return int(bit_str, 2)

    def generate_session_key(self) -> bytes:
        """
        Generate a 256-bit (32-byte) session key using the 8-qubit generator.
        """
        return bytes([self.generate_quantum_byte() for _ in range(32)])
