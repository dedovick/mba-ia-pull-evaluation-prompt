"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import os
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


SEED_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = "prompts/bug_to_user_story_v1.yml"

def _str_presenter(dumper, data):
    """Grava textos multilinha no estilo bloco (|), mais legível para prompts."""
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(str, _str_presenter)

ROLE_TO_FIELD = {
    "SystemMessagePromptTemplate": "system_prompt",
    "HumanMessagePromptTemplate": "user_prompt",
}


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt semente no LangSmith Hub e converte para o formato YAML local.

    Returns:
        Dicionário no formato {nome_do_prompt: {...campos...}} ou None se erro
    """
    try:
        client = Client()
        print(f"   Puxando prompt: {SEED_PROMPT}")
        prompt = client.pull_prompt(SEED_PROMPT, dangerously_pull_public_prompt=True)
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt '{SEED_PROMPT}': {e}")
        return None

    prompt_name = SEED_PROMPT.split("/")[-1]
    prompt_data = {"description": "Prompt para converter relatos de bugs em User Stories"}

    for message in prompt.messages:
        field = ROLE_TO_FIELD.get(type(message).__name__)
        if field:
            prompt_data[field] = message.prompt.template

    hub_metadata = prompt.metadata or {}
    prompt_data.update({
        "version": "v1",
        "source": SEED_PROMPT,
        "commit_hash": hub_metadata.get("lc_hub_commit_hash", ""),
        "input_variables": prompt.input_variables,
        "tags": ["bug-analysis", "user-story", "product-management"],
    })

    return {prompt_name: prompt_data}


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    prompts = pull_prompts_from_langsmith()
    if not prompts:
        return 1

    if not save_yaml(prompts, OUTPUT_FILE):
        return 1

    print(f"   ✓ Prompt salvo em {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
