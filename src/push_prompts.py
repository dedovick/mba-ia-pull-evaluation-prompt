"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()


PROMPT_FILE = "prompts/bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"
INPUT_VARIABLE = "{bug_report}"


def _escape_braces(text: str) -> str:
    """Escapa chaves de texto fixo para o ChatPromptTemplate não tratá-las como variáveis."""
    return text.replace("{", "{{").replace("}", "}}")


def build_prompt_template(prompt_data: dict) -> ChatPromptTemplate:
    """
    Monta o ChatPromptTemplate: system -> pares few-shot (user/assistant) -> user.

    Os exemplos few-shot viram mensagens reais de conversa, que é como modelos de chat
    aprendem melhor o formato esperado.
    """
    messages = [("system", _escape_braces(prompt_data["system_prompt"]))]

    for example in prompt_data.get("few_shot_examples", []):
        messages.append(("human", _escape_braces(example["input"])))
        messages.append(("ai", _escape_braces(example["output"])))

    messages.append(("human", prompt_data["user_prompt"]))
    return ChatPromptTemplate.from_messages(messages)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB")
    full_name = f"{username}/{prompt_name}"
    techniques = prompt_data.get("techniques_applied", [])

    try:
        prompt = build_prompt_template(prompt_data)
        client = Client()
        url = client.push_prompt(
            full_name,
            object=prompt,
            is_public=True,
            description=prompt_data.get("description", ""),
            readme="Técnicas aplicadas:\n" + "\n".join(f"- {t}" for t in techniques),
            tags=list(dict.fromkeys(prompt_data.get("tags", []) + [prompt_data.get("version", "")])),
        )
    except Exception as e:
        if "Nothing to commit" in str(e):
            print(f"   ℹ️  {full_name} já está atualizado (nenhuma mudança no prompt)")
            return True
        print(f"❌ Erro ao fazer push de '{full_name}': {e}")
        return False

    print(f"   ✓ Push realizado: {full_name}")
    print(f"     Técnicas: {', '.join(techniques)}")
    print(f"     {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, errors = validate_prompt_structure(prompt_data)

    if INPUT_VARIABLE not in prompt_data.get("user_prompt", ""):
        errors.append(f"user_prompt deve conter a variável {INPUT_VARIABLE}")
    if INPUT_VARIABLE in prompt_data.get("system_prompt", ""):
        errors.append(f"{INPUT_VARIABLE} deve ficar apenas no user_prompt")

    examples = prompt_data.get("few_shot_examples", [])
    if len(examples) < 2:
        errors.append(f"Few-shot exige pelo menos 2 exemplos, encontrados: {len(examples)}")
    for i, example in enumerate(examples):
        if not example.get("input") or not example.get("output"):
            errors.append(f"Exemplo few-shot {i} precisa de 'input' e 'output'")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS PARA O LANGSMITH")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(PROMPT_FILE)
    if not data or PROMPT_KEY not in data:
        print(f"❌ Prompt '{PROMPT_KEY}' não encontrado em {PROMPT_FILE}")
        return 1

    prompt_data = data[PROMPT_KEY]
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    return 0 if push_prompt_to_langsmith(PROMPT_KEY, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
