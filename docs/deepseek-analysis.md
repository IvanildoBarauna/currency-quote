# currency-quote — Análise de código e plano de refatoração

> **Status:** proposta de trabalho (este PR é somente documentação; nenhuma alteração funcional foi feita).
>
> **Data da análise:** 2026-11-05
>
> **Base:** `origin/main` @ `12a2eca`
>
> **Branch:** `docs/deepseek-analysis`
>
> **Autor da análise:** DeepSeek V4.1 Flash Free (OpenCode)

---

## 1. Sumário executivo

A `currency-quote` tem uma base organizada, testes passando e uma API pública simples. O caminho feliz funciona, mas a biblioteca ainda não está preparada para uso prolongado em produção nem para crescer em adoção.

Os três problemas de maior impacto são:

1. **Confiabilidade:** existem bugs que quebram o fluxo em situações comuns, como consultar um feriado/fim de semana, e um campo de timestamp que fica congelado no import.
2. **Custo de instalação:** o wheel tem cerca de **12,5 KB**, mas a instalação arrasta **pandas + numpy (~73 MB no ambiente local)** e instala `pytest` em produção. Isso é uma barreira enorme para serverless, containers e CI.
3. **Descoberta e conversão:** metadata do PyPI incompleta/errada, README sem instrução de instalação, changelog desatualizado e tópicos do GitHub que não falam de câmbio.

A arquitetura hexagonal é um bom ativo, porém hoje está apenas no desenho: os use cases instanciam adapters concretos e o domínio importa um use case. Isso impede trocar provedores, dificulta testes e bloqueia evoluções como cache e multi-provider.

A recomendação é executar o plano em fases, começando por uma rede de segurança de testes e pelos bugs de confiabilidade, depois removendo o peso de instalação e invertendo as dependências, e só então adicionando funcionalidades que aumentam adoção (conversão, intervalo histórico, CLI e documentação).

---

## 2. Baseline verificado

| Item | Resultado |
|---|---|
| Testes | 29 passando em ~0,86 s |
| Cobertura total | 90% (incluindo os próprios testes) |
| `currency_api.py` | 50% |
| `currency_validator_api.py` | 53% |
| `lib_controller.py` | 65% |
| Wheel publicado | `currency_quote-5.0.7-py3-none-any.whl` — 12.508 bytes |
| Dependências de runtime | `api-to-dataframe` + `pytest` |
| Tamanho de pandas no venv local | ~49 MB |
| Tamanho de numpy no venv local | ~24 MB |
| Python no CI | apenas 3.9 (já fora do suporte oficial) |
| Última publicação no PyPI | 2026-05-11 |

Comandos usados como evidência:

```bash
poetry run pytest -q
poetry run coverage run -m pytest && poetry run coverage report -m
poetry show --tree
curl -s https://pypi.org/pypi/currency-quote/json
```

---

## 3. Achados

### 3.1 P0 — Bugs de confiabilidade

#### 3.1.1 `quote_extracted_at` fica congelado no import

**Arquivo:** `src/currency_quote/domain/entities/currency.py:47`

```python
quote_extracted_at: int = int(datetime.now().timestamp())
```

O valor padrão de uma dataclass é avaliado uma única vez, quando a classe é definida. Consequência: todas as cotações criadas sem passar o campo explicitamente compartilham o mesmo timestamp, mesmo que sejam extraídas horas depois.

**Evidência:** duas instâncias criadas com 1,2 s de diferença retornaram o mesmo valor.

**Correção proposta:**

```python
from dataclasses import dataclass, field

quote_extracted_at: int = field(
    default_factory=lambda: int(datetime.now().timestamp())
)
```

**Critério de aceite:** teste que cria duas instâncias em momentos distintos e verifica timestamps diferentes.

---

#### 3.1.2 `get_history_quote` quebra quando não há cotação na data

**Arquivo:** `src/currency_quote/adapters/outbound/currency_api.py:71-77`

O adapter assume que a API sempre retorna uma lista com pelo menos um item e acessa `response[0]`. Em fins de semana e feriados, a AwesomeAPI retorna `[]`, provocando `IndexError`.

**Evidência:** consulta real para `2026-11-01` (domingo) retornou `[]` e a biblioteca levantou `IndexError: list index out of range`.

**Correção proposta:**

- Validar a resposta antes de acessar índices.
- Definir uma exceção de domínio, por exemplo `QuoteNotFoundError`, para o caso de um único par.
- Para múltiplos pares, decidir entre retorno parcial com log de aviso ou falha estrita configurável (`strict=True`).
- Documentar o comportamento para datas sem pregão.

**Critério de aceite:** testes com resposta vazia, resposta malformada e lote misto (um par com cotação, outro sem).

---

#### 3.1.3 Preços com tipos inconsistentes

**Arquivo:** `src/currency_quote/adapters/outbound/currency_api.py:38-39` e `:75-76`

Na cotação atual, `bid` e `ask` são repassados como strings. Na histórica, são convertidos para `float`. A dataclass declara `float` nos dois casos, e o README mostra a inconsistência.

**Impacto:** operações aritméticas com a última cotação podem falhar ou concatenar strings.

**Correção proposta:** converter sempre para `float` no adapter e adicionar teste de tipo.

**Critério de aceite:** `isinstance(quote["bid_price"], float)` e `isinstance(quote["ask_price"], float)` para os dois endpoints.

---

#### 3.1.4 Datas inválidas e timezone

**Arquivo:** `src/currency_quote/adapters/outbound/currency_api.py:47-55`

A validação atual verifica apenas tamanho e se a data é maior/igual a hoje. Ela aceita datas impossíveis de 8 dígitos (`20261399`) e usa `datetime.today()` no timezone local, enquanto a fonte pode operar em outro timezone.

**Correção proposta:**

- Aceitar `datetime.date`, `str` e `int` (mantendo compatibilidade).
- Normalizar com `datetime.strptime` e capturar `ValueError`.
- Usar o timezone da fonte (`America/Sao_Paulo`) para a regra de "hoje".
- Levantar `ValueError` claro em vez de retornar `[]` silenciosamente.

**Critério de aceite:** testes com data inexistente, data futura, data de hoje, string e objeto `date`.

---

#### 3.1.5 `pytest` como dependência de produção

**Arquivo:** `pyproject.toml:32`

`pytest` aparece em `[tool.poetry.dependencies]` e, portanto, é instalado para todos os usuários. O metadata do PyPI confirma `Requires-Dist: pytest`.

**Correção proposta:** remover de produção e manter apenas no grupo `dev`.

**Critério de aceite:** `pip install .` em ambiente limpo não instala `pytest`.

---

#### 3.1.6 Efeito colateral de logging no import

**Arquivos:** `src/currency_quote/__init__.py:5`, `src/currency_quote/utils/logger.py:4-21`

O pacote configura handler e nível de log no momento do import. Bibliotecas não devem controlar o logging global da aplicação.

**Correção proposta:**

- Usar `logging.getLogger(__name__).addHandler(logging.NullHandler())`.
- Remover `setup_logging()` do `__init__.py`.
- Expor uma função opcional de configuração, caso o usuário queira usá-la.

**Critério de aceite:** importar a lib não adiciona handlers nem altera o nível de log da aplicação.

---

#### 3.1.7 Configuração morta

**Arquivo:** `src/currency_quote/config/endpoints.py:6-7`

`RETRY_TIME_SECONDS` e `RETRY_ATTEMPTS` não são usados. Os valores efetivos vêm dos defaults do `api-to-dataframe` (3 tentativas e timeout de 10 s).

**Correção proposta:** remover as constantes ou conectá-las a uma configuração real do cliente (`timeout`, `retries`, `initial_delay`, `base_url`).

---

### 3.2 P1 — Arquitetura e API

#### 3.2.1 Inversão de dependência incompleta

**Arquivos:**

- `src/currency_quote/domain/services/get_currency_quote.py:5-7`
- `src/currency_quote/application/use_cases/get_last_currency_quote.py:3,12`
- `src/currency_quote/application/use_cases/get_history_currency_quote.py:3,14`
- `src/currency_quote/application/use_cases/validate_currency.py:3,11`

Problemas:

- O domínio importa `application.use_cases.validate_currency` — dependência na direção errada.
- Os use cases importam `CurrencyAPI` diretamente, então trocar o provedor exige editar regra de aplicação.
- `GetCurrencyQuoteService` recebe `Type[ICurrencyRepository]` (a classe), não uma instância/fábrica explícita.
- O `ClientBuilder` não permite injetar repositório ou validador.

**Impacto:** a arquitetura hexagonal não entrega o benefício prometido; testes dependem de `patch` em caminhos internos; cache e multi-provider ficam difíceis.

**Refatoração proposta:**

```text
ClientBuilder (composition root)
  ├── cria CurrencyValidatorAPI
  ├── cria CurrencyAPI
  └── injeta nos use cases
        └── services dependem apenas de ICurrencyRepository / ICurrencyValidator
```

Passos:

1. Mover a orquestração de validação para o use case ou injetar o validador no serviço.
2. Fazer use cases receberem instâncias das portas.
3. Fazer `ClientBuilder` montar as dependências e permitir overrides opcionais.
4. Remover imports de adapters de dentro de `application/`.
5. Substituir `patch` de métodos internos por fakes nos testes.

**Critério de aceite:** um teste consegue usar um repositório fake em memória sem `patch` e sem rede.

---

#### 3.2.2 Exceções de domínio

Hoje o usuário recebe `ValueError`, `IndexError`, `KeyError` ou exceções genéricas do HTTP. Proposta:

```python
class CurrencyQuoteError(Exception): ...
class InvalidCurrencyError(CurrencyQuoteError, ValueError): ...
class QuoteNotFoundError(CurrencyQuoteError): ...
class ProviderError(CurrencyQuoteError): ...
```

Isso melhora a experiência de quem integra e permite tratamento seletivo.

---

#### 3.2.3 Tipagem pública

- Adicionar `py.typed` ao pacote (PEP 561).
- Tipar retornos e parâmetros com precisão (`list[CurrencyQuote]`, `dict[str, Any]`, `date | str | int`).
- Corrigir `IController`, que declara retorno `dict` mas os métodos retornam `list`.
- Adicionar docstrings nos métodos públicos.
- Rodar `mypy` ou `pyright` no CI.

---

#### 3.2.4 Normalização de entrada

`CurrencyObject` poderia:

- Converter pares para maiúsculo.
- Remover espaços nas extremidades.
- Remover duplicatas preservando a ordem.
- Validar que cada item é string (hoje um item não-string pode gerar `AttributeError`).
- Corrigir a mensagem que fala em 3 caracteres, mas aceita 3 ou 4.

---

#### 3.2.5 Cache da validação

Cada `get_last_quote()` consulta `/json/available` antes de buscar a cotação. Isso dobra requisições, latência e pontos de falha.

Proposta:

- Cachear os pares disponíveis por TTL (por exemplo, 1 hora ou 24 horas).
- Ou permitir `validate=False`.
- Ou validar apenas o formato localmente por padrão, com validação online opcional.

---

#### 3.2.6 Configuração do cliente

Adicionar parâmetros (ou objeto de configuração):

```python
ClientBuilder(
    currency_list="USD-BRL",
    timeout=10,
    retries=3,
    initial_delay=1,
    validate=True,
    base_url=None,
    cache_ttl=3600,
)
```

Isso também facilita testes de integração e uso atrás de proxy.

---

### 3.3 P1 — Empacotamento e distribuição

#### 3.3.1 Dependência pesada

`api-to-dataframe` é usado apenas para requisições HTTP e retry, mas traz pandas e numpy. Para uma lib de cotações, isso não se justifica.

**Proposta:**

- Substituir por `requests` ou `httpx` + `tenacity` (ou retry próprio pequeno).
- Reutilizar `requests.Session` para connection pooling.
- Oferecer pandas como extra opcional:

```bash
pip install currency-quote
pip install currency-quote[pandas]
```

**Meta:** reduzir o install de ~73 MB para algo próximo de 1–5 MB.

---

#### 3.3.2 Metadata do PyPI

Problemas atuais:

- `Keywords: None`.
- `Homepage`, `Repository` e `Issues` apontam para `currency-quote-wrapper`, nome antigo.
- Descrição longa com jargões, sem foco em busca.
- Classifier de Python 3.8, incompatível com `requires-python >=3.9`.
- Ausência de `Typing :: Typed`.

**Proposta de descrição:**

> Simple Python client for Brazilian currency exchange rates — last and historical quotes for USD/BRL, EUR/BRL and 500+ pairs.

**Keywords sugeridas:** `currency`, `exchange-rate`, `forex`, `quotes`, `brazil`, `awesomeapi`, `finance`.

---

#### 3.3.3 README

O README não tem seção de instalação. Para conversão de downloads, incluir:

- `## Installation` com `pip`, `poetry` e `uv`.
- Exemplo mínimo com resposta real.
- Tabela de pares suportados (a API tem 540 pares, incluindo cripto).
- Tratamento de erros e exceções.
- Configuração de timeout/retries/cache.
- Comportamento em fins de semana e feriados.
- CLI, quando existir.
- Versões de Python suportadas.
- Link para documentação e para o repositório canônico.

---

#### 3.3.4 CI/CD e releases

- CI testa apenas Python 3.9. Criar matriz 3.10–3.14 e definir o mínimo oficial.
- Adicionar `ruff`, `mypy`/`pyright`, `poetry build` e `twine check`.
- CD dispara em qualquer PR fechado, sem verificar `merged == true`. Ajustar para tags/releases.
- Migrar de `PYPI_TOKEN` para Trusted Publishing (OIDC).
- Corrigir `CHANGELOG.md`: está parado na 4.0.0, enquanto o PyPI está na 5.0.7; os links usam `me.github.com`.
- Automatizar changelog/release notes.

---

#### 3.3.5 Descoberta no GitHub

Topics atuais: `data-analysis`, `data-analytics`, `data-engineering`, `library`, `portfolio-display`, `pypi-packages`, `python`.

Adicionar/trocar por: `currency`, `exchange-rate`, `forex`, `currency-converter`, `brazil`, `awesomeapi`, `finance`.

Também vale adicionar social preview, descrição objetiva e um GIF/print do uso.

---

### 3.4 P2 — Testes e qualidade

Os testes atuais passam, mas não cobrem o miolo dos adapters e alguns são tautológicos:

- `src/tests/test_get_history_currency_quote.py:13-47` faz `patch` do próprio método que deveria testar.
- `src/tests/test_lib_controller.py:49-62` mocka o use case e verifica apenas que o retorno é `[]`.

**Proposta:**

- Configurar coverage com `source = ["currency_quote"]` e `fail_under`.
- Testar parsing de `/last` e `/json/daily` com respostas fixas.
- Testar resposta vazia, JSON inválido, campo faltando, HTTP 429/500 e timeout.
- Testar `quote_extracted_at` (duas instâncias).
- Testar preços como `float`.
- Testar pares de 4 caracteres (`USD-BRLT`), duplicados, minúsculos e com espaço.
- Testar lotes mistos (válidos + inválidos; com cotação + sem cotação).
- Usar `responses` ou `requests-mock` para HTTP.
- Substituir mocks internos por fakes injetados após a refatoração de DI.

---

## 4. Arquitetura alvo

```text
currency_quote/
├── adapters/
│   ├── inbound/
│   │   ├── lib_controller.py      # ClientBuilder: composition root + API pública
│   │   └── cli.py                 # novo: entrypoint de linha de comando
│   └── outbound/
│       ├── awesomeapi/
│       │   ├── currency_api.py
│       │   └── validator_api.py
│       └── ...
├── application/
│   ├── ports/
│   │   ├── inbound/
│   │   └── outbound/
│   └── use_cases/
├── domain/
│   ├── entities/
│   ├── services/
│   └── exceptions.py              # novo
├── config/
└── utils/
```

Regras:

- `domain/` não importa `application/` nem `adapters/`.
- `application/use_cases` depende apenas de portas.
- `adapters/` implementa as portas.
- `ClientBuilder` é o único ponto de composição.
- Nenhum módulo importado pelo usuário configura logging global.

---

## 5. Plano de execução

### Fase 0 — Rede de segurança (1 dia)

- [ ] Configurar coverage para medir apenas `src/currency_quote`.
- [ ] Adicionar testes dos adapters com respostas fixas.
- [ ] Adicionar testes de erros: resposta vazia, JSON inválido, HTTP 429/500, timeout.
- [ ] Adicionar matriz de Python no CI (3.10–3.14).
- [ ] Adicionar `ruff` e `mypy`/`pyright` ao CI.
- [ ] Adicionar `poetry build` + `twine check` ao CI.

**Saída:** CI confiável o suficiente para refatorar sem medo.

### Fase 1 — Correções P0 (1–2 dias)

- [ ] Corrigir `quote_extracted_at` com `default_factory`.
- [ ] Tratar resposta vazia no histórico com exceção clara/retorno parcial documentado.
- [ ] Converter `bid`/`ask` para `float` também na última cotação.
- [ ] Validar datas com `datetime` e timezone da fonte.
- [ ] Remover `setup_logging()` do import e usar `NullHandler`.
- [ ] Mover `pytest` para o grupo de desenvolvimento.
- [ ] Adicionar `py.typed`.
- [ ] Remover ou conectar as constantes de retry mortas.
- [ ] Atualizar README com instalação, erros e limitações.
- [ ] Corrigir metadata do PyPI (`keywords`, URLs, classifiers).

**Saída:** versão 5.0.x ou 5.1.0 confiável, sem mudanças que quebrem a API pública.

### Fase 2 — Pacote leve e injeção de dependências (1–2 semanas)

- [ ] Substituir `api-to-dataframe` por HTTP leve (`requests`/`httpx` + retry).
- [ ] Reutilizar sessão/conexão e expor `timeout`/`retries`.
- [ ] Refatorar use cases para receber portas injetadas.
- [ ] Transformar `ClientBuilder` no composition root.
- [ ] Remover imports de adapters de `application/`.
- [ ] Adicionar exceções de domínio.
- [ ] Cachear validação de pares com TTL configurável.
- [ ] Reescrever testes com fakes em memória.

**Saída:** instalação leve, arquitetura realmente desacoplada e testável.

### Fase 3 — DX e API tipada (1 semana)

- [ ] Normalizar entrada (maiúsculas, espaços, duplicatas, tipos).
- [ ] Aceitar `date`/`str`/`int` em métodos históricos.
- [ ] Tipar retornos públicos e corrigir `IController`.
- [ ] Adicionar docstrings nos métodos públicos.
- [ ] Oferecer retorno tipado opcional (`CurrencyQuote`), mantendo dicts por compatibilidade.
- [ ] Adicionar alias `CurrencyQuoteClient` para o nome `ClientBuilder`.

**Saída:** autocomplete melhor, menos erros de uso e API mais previsível.

### Fase 4 — Funcionalidades de adoção (2–4 semanas)

- [ ] `client.convert(amount, from_currency, to_currency)`.
- [ ] `client.get_history_range(start, end)` ou últimos N dias.
- [ ] `client.get_available_currencies()`.
- [ ] Fallback para última cotação disponível em fins de semana/feriados.
- [ ] CLI (`currency-quote USD-BRL --history 2024-01-01`), com `__main__.py` correto.
- [ ] Extra opcional `[pandas]` com `to_dataframe()`.
- [ ] Cliente async opcional (`httpx`).
- [ ] Providers alternativos (Banco Central, Frankfurter) usando a arquitetura de portas.

**Saída:** novos motivos para usar e compartilhar a lib.

### Fase 5 — Crescimento e documentação (contínuo)

- [ ] Docs site (MkDocs Material + GitHub Pages).
- [ ] Tutorial: “Como obter cotação do dólar em Python”.
- [ ] Demo no Google Colab ou notebook executável.
- [ ] Divulgação em comunidades (Dev.to, Medium, LinkedIn, Python Brasil, Stack Overflow).
- [ ] Inclusão em listas “awesome” de Python/finanças.
- [ ] Publicação no conda-forge.
- [ ] Releases frequentes com changelog automático.
- [ ] Issue templates e política de suporte/versionamento.

**Saída:** mais descoberta e retenção, não apenas downloads pontuais.

---

## 6. Compatibilidade e versionamento

- Manter `ClientBuilder`, `get_last_quote()` e `get_history_quote()` funcionando.
- Manter retorno em `list[dict]` durante a fase de transição.
- Adicionar novos métodos/retornos tipados de forma aditiva.
- Reservar mudanças de assinatura e remoção de comportamentos para uma major (`6.0.0`), com guia de migração.
- Documentar claramente o comportamento de datas sem cotação e de pares inválidos.

---

## 7. Métricas de sucesso

| Métrica | Meta |
|---|---|
| Tamanho de instalação | < 5 MB (sem extras) |
| Dependências de runtime | ≤ 2 (HTTP + retry) |
| Cobertura dos adapters | ≥ 90% |
| Tempo de `get_last_quote()` | reduzir ~50% ao cachear validação |
| Python suportado | mínimo definido e testado em matriz |
| Releases | pelo menos 1 por mês durante a fase ativa |
| Downloads no PyPI | tendência de alta semanal (métrica ruidosa; acompanhar junto de stars/issues) |

---

## 8. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Quebrar usuários existentes | Mudanças aditivas primeiro; major apenas com migração documentada |
| Troca de HTTP introduzir regressão | Testes de contrato com respostas fixas antes da troca |
| Cache mascarar mudanças de pares | TTL curto/configurável e opção `validate=False` |
| Provider mudar resposta | Testes de contrato + validação de schema no adapter |
| Aumento de escopo | Executar fases em PRs pequenos e independentes |

---

## 9. Fora de escopo deste plano

- Reescrever a API pública do zero.
- Criar um serviço hospedado ou dashboard.
- Suporte a múltiplos provedores na primeira fase.
- Observabilidade avançada (OpenTelemetry, métricas Prometheus).

---

## 10. Apêndice — evidências da análise

```text
$ poetry run pytest -q
............................. [100%]
29 passed in 0.86s

$ poetry run coverage report -m
...
src/currency_quote/adapters/outbound/currency_api.py      34   17   50%
src/currency_quote/adapters/outbound/currency_validator_api.py 15 7 53%
src/currency_quote/adapters/inbound/lib_controller.py     23    8   65%
TOTAL                                                    475   46   90%
```

```text
$ curl https://pypi.org/pypi/currency-quote/json
Name: currency-quote
Version: 5.0.7
Requires-Python: >=3.9,<4.0
Requires-Dist: api-to-dataframe, pytest
Keywords: None
Project-URL: Homepage, https://pypi.org/project/currency-quote-wrapper
```

```text
$ poetry show --tree
api-to-dataframe 2.0.0
├── pandas >=2.2.3,<3.0.0
│   ├── numpy ...
│   └── ...
└── requests >=2.32.3,<3.0.0
```

Consulta real que demonstra o bug de fim de semana:

```text
GET /json/daily/USD-BRL?start_date=20261101&end_date=20261101
200 []
```

Depois:

```text
IndexError: list index out of range
```
