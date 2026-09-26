"""
Testes automatizados para validação de prompts.
"""
import re

import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    """Dados do prompt otimizado (v2)."""
    data = load_prompts(PROMPT_FILE)
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


def all_prompt_text(prompt: dict) -> str:
    """Concatena todo o texto enviado ao modelo: system, user e exemplos few-shot."""
    parts = [prompt.get("system_prompt", ""), prompt.get("user_prompt", "")]
    for example in prompt.get("few_shot_examples", []) or []:
        parts += [example.get("input", ""), example.get("output", "")]
    return "\n".join(parts)


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt
        assert isinstance(prompt["system_prompt"], str)
        assert prompt["system_prompt"].strip()

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(r"\bvocê é (um|uma)\b", prompt["system_prompt"], re.IGNORECASE), \
            "system_prompt deve definir uma persona começando com 'Você é um/uma ...'"

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system = prompt["system_prompt"].lower()
        assert "como um" in system and "eu quero" in system and "para que" in system, \
            "system_prompt deve exigir o formato 'Como um ..., eu quero ..., para que ...'"
        assert "critérios de aceitação" in system
        assert "dado que" in system and "quando" in system and "então" in system, \
            "system_prompt deve exigir critérios no formato Dado/Quando/Então"

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        examples = prompt.get("few_shot_examples")
        assert isinstance(examples, list) and len(examples) >= 2, \
            "Few-shot exige pelo menos 2 exemplos em 'few_shot_examples'"
        for i, example in enumerate(examples):
            assert str(example.get("input", "")).strip(), f"Exemplo {i} sem 'input'"
            assert str(example.get("output", "")).strip(), f"Exemplo {i} sem 'output'"
            assert "Como um" in example["output"], f"Exemplo {i}: saída fora do formato User Story"

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        assert "TODO" not in all_prompt_text(prompt).upper()

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])
        assert isinstance(techniques, list)
        assert len(techniques) >= 2, f"Mínimo de 2 técnicas, encontradas: {len(techniques)}"
        assert any("few" in t.lower() for t in techniques), "Few-shot Learning é obrigatório"

    def test_bug_report_only_in_user_prompt(self, prompt):
        """A variável {bug_report} deve ir só no user prompt (erro intencional do v1)."""
        assert "{bug_report}" in prompt.get("user_prompt", "")
        assert "{bug_report}" not in prompt["system_prompt"]

    def test_prompt_structure_is_valid(self, prompt):
        """Usa a validação oficial de utils.py (campos obrigatórios, TODOs, técnicas)."""
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, errors


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
