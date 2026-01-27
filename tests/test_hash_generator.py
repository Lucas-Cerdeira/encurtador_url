import pytest
from utils.hash_generator import HashGenerator


def test_hash_generator_init_default():
    """Testa inicialização com tamanho padrão."""
    generator = HashGenerator()
    assert generator.default_size == 6


def test_hash_generator_init_custom_size():
    """Testa inicialização com tamanho customizado."""
    generator = HashGenerator(default_size=4)
    assert generator.default_size == 4


def test_hash_generator_init_invalid_size_too_large():
    """Testa inicialização com tamanho maior que o máximo."""
    with pytest.raises(ValueError) as exc:
        HashGenerator(default_size=7)
    assert "6" in str(exc.value)


def test_hash_generator_init_invalid_size_too_small():
    """Testa inicialização com tamanho menor que o mínimo."""
    with pytest.raises(ValueError) as exc:
        HashGenerator(default_size=0)
    assert "1" in str(exc.value)


def test_hash_generator_generate_default_size():
    """Testa geração de hash com tamanho padrão."""
    generator = HashGenerator(default_size=6)
    hash_code = generator.generate()
    
    assert len(hash_code) == 6
    assert all(char in HashGenerator.BASE62_ALPHABET for char in hash_code)


def test_hash_generator_generate_custom_size():
    """Testa geração de hash com tamanho customizado."""
    generator = HashGenerator()
    hash_code = generator.generate(size=4)
    
    assert len(hash_code) == 4
    assert all(char in HashGenerator.BASE62_ALPHABET for char in hash_code)


def test_hash_generator_generate_different_hashes():
    """Testa que hashes gerados são diferentes (probabilidade muito alta)."""
    generator = HashGenerator()
    hash1 = generator.generate(size=6)
    hash2 = generator.generate(size=6)
    hash3 = generator.generate(size=6)
    
    # É extremamente improvável que sejam iguais (1 em 56 bilhões)
    assert hash1 != hash2 or hash2 != hash3 or hash1 != hash3


def test_hash_generator_generate_invalid_size():
    """Testa geração com tamanho inválido."""
    generator = HashGenerator()
    
    with pytest.raises(ValueError) as exc:
        generator.generate(size=7)
    assert "6" in str(exc.value)
    
    with pytest.raises(ValueError) as exc:
        generator.generate(size=0)
    assert "1" in str(exc.value)


def test_hash_generator_validate_valid_hash():
    """Testa validação de hash válido."""
    generator = HashGenerator()
    
    assert generator.validate("aB3xY9") is True
    assert generator.validate("ABC123") is True
    assert generator.validate("xyz789") is True
    assert generator.validate("A") is True  # Tamanho mínimo


def test_hash_generator_validate_invalid_hash():
    """Testa validação de hash inválido."""
    generator = HashGenerator()
    
    # Hash muito longo
    assert generator.validate("aB3xY9Z") is False
    
    # Caracteres inválidos
    assert generator.validate("aB3-xY9") is False  # Contém hífen
    assert generator.validate("aB3 xY9") is False  # Contém espaço
    assert generator.validate("aB3@xY9") is False  # Contém @
    
    # Hash vazio
    assert generator.validate("") is False


def test_hash_generator_validate_edge_cases():
    """Testa casos extremos de validação."""
    generator = HashGenerator()
    
    # Tamanho máximo (6 caracteres)
    assert generator.validate("aB3xY9") is True
    
    # Tamanho mínimo (1 caractere)
    assert generator.validate("A") is True
    assert generator.validate("z") is True
    assert generator.validate("9") is True


def test_hash_generator_get_max_combinations():
    """Testa cálculo de combinações máximas."""
    # 6 caracteres: 62^6 = 56.800.235.584
    assert HashGenerator.get_max_combinations(6) == 62 ** 6
    
    # 1 caractere: 62^1 = 62
    assert HashGenerator.get_max_combinations(1) == 62
    
    # 3 caracteres: 62^3 = 238.328
    assert HashGenerator.get_max_combinations(3) == 62 ** 3


def test_hash_generator_get_max_combinations_invalid_size():
    """Testa cálculo de combinações com tamanho inválido."""
    with pytest.raises(ValueError):
        HashGenerator.get_max_combinations(7)
    
    with pytest.raises(ValueError):
        HashGenerator.get_max_combinations(0)


def test_hash_generator_get_alphabet():
    """Testa retorno do alfabeto Base 62."""
    alphabet = HashGenerator.get_alphabet()
    
    assert len(alphabet) == 62
    assert all(char.isupper() or char.islower() or char.isdigit() for char in alphabet)
    assert "A" in alphabet
    assert "Z" in alphabet
    assert "a" in alphabet
    assert "z" in alphabet
    assert "0" in alphabet
    assert "9" in alphabet


def test_hash_generator_all_characters_in_alphabet():
    """Testa que todos os caracteres gerados estão no alfabeto."""
    generator = HashGenerator()
    
    # Gera vários hashes e verifica que todos os caracteres são válidos
    for _ in range(100):
        hash_code = generator.generate(size=6)
        assert all(char in HashGenerator.BASE62_ALPHABET for char in hash_code)


def test_hash_generator_size_range():
    """Testa geração de hash em todos os tamanhos válidos."""
    generator = HashGenerator()
    
    for size in range(1, 7):  # 1 a 6
        hash_code = generator.generate(size=size)
        assert len(hash_code) == size
        assert generator.validate(hash_code) is True
