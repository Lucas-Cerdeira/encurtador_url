import secrets
import string
from typing import Optional


class HashGenerator:
    """
    Gerador de hash usando Base 62 (A-Z, a-z, 0-9).
    
    Características:
    - Alfabeto: 62 caracteres (26 maiúsculas + 26 minúsculas + 10 números)
    - Tamanho máximo: 6 caracteres
    - Geração segura usando secrets.SystemRandom()
    - Escalável para diferentes tamanhos
    
    Exemplo:
        generator = HashGenerator()
        hash_code = generator.generate(size=6)  # Ex: "aB3xY9"
    """
    
    # Alfabeto Base 62: A-Z (26) + a-z (26) + 0-9 (10) = 62 caracteres
    BASE62_ALPHABET = string.ascii_uppercase + string.ascii_lowercase + string.digits
    
    # Tamanho máximo permitido (6 caracteres)
    MAX_SIZE = 6
    
    # Tamanho mínimo permitido (1 caractere)
    MIN_SIZE = 1
    
    def __init__(self, default_size: int = 6):
        """
        Inicializa o gerador de hash.
        
        Args:
            default_size: Tamanho padrão do hash (padrão: 6)
            
        Raises:
            ValueError: Se default_size estiver fora dos limites permitidos
        """
        if not (self.MIN_SIZE <= default_size <= self.MAX_SIZE):
            raise ValueError(
                f"Tamanho deve estar entre {self.MIN_SIZE} e {self.MAX_SIZE} caracteres"
            )
        self.default_size = default_size
        self._random = secrets.SystemRandom()
    
    def generate(self, size: Optional[int] = None) -> str:
        """
        Gera um hash aleatório usando Base 62.
        
        Args:
            size: Tamanho do hash a ser gerado (padrão: default_size)
                 Se None, usa o tamanho padrão configurado.
        
        Returns:
            String com o hash gerado (ex: "aB3xY9")
            
        Raises:
            ValueError: Se size estiver fora dos limites permitidos
        """
        if size is None:
            size = self.default_size
        
        if not (self.MIN_SIZE <= size <= self.MAX_SIZE):
            raise ValueError(
                f"Tamanho deve estar entre {self.MIN_SIZE} e {self.MAX_SIZE} caracteres"
            )
        
        # Gera hash usando SystemRandom para segurança criptográfica
        hash_code = ''.join(
            self._random.choice(self.BASE62_ALPHABET) for _ in range(size)
        )
        
        return hash_code
    
    def validate(self, hash_code: str) -> bool:
        """
        Valida se um hash_code está no formato correto (Base 62, até MAX_SIZE caracteres).
        
        Args:
            hash_code: Código hash a ser validado
        
        Returns:
            True se válido, False caso contrário
        """
        if not hash_code:
            return False
        
        if len(hash_code) > self.MAX_SIZE:
            return False
        
        # Verifica se todos os caracteres estão no alfabeto Base 62
        return all(char in self.BASE62_ALPHABET for char in hash_code)
    
    @classmethod
    def get_max_combinations(cls, size: int) -> int:
        """
        Calcula o número máximo de combinações possíveis para um tamanho dado.
        
        Args:
            size: Tamanho do hash
        
        Returns:
            Número de combinações possíveis (62^size)
        """
        if not (cls.MIN_SIZE <= size <= cls.MAX_SIZE):
            raise ValueError(
                f"Tamanho deve estar entre {cls.MIN_SIZE} e {cls.MAX_SIZE} caracteres"
            )
        return 62 ** size
    
    @classmethod
    def get_alphabet(cls) -> str:
        """
        Retorna o alfabeto Base 62 usado pelo gerador.
        
        Returns:
            String com todos os caracteres válidos (A-Z, a-z, 0-9)
        """
        return cls.BASE62_ALPHABET
