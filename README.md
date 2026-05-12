# Testes de Desempenho — Link Extractor

Trabalho prático de **Testes de Desempenho** realizado com a aplicação [Link Extractor](https://github.com/ibnesayeed/linkextractor), utilizando a ferramenta [Locust](https://locust.io/) para geração de carga e análise comparativa entre versões Python e Ruby do serviço de extração de links, com e sem cache Redis.

---

## Descrição do Projeto

A aplicação **Link Extractor** oferece um front-end web (PHP) que extrai e exibe todos os links presentes em uma página web fornecida como URL. Sua arquitetura é composta por três serviços containerizados via Docker:

| Serviço | Tecnologia | Descrição |
|---------|-----------|-----------|
| **Web App** | PHP | Front-end web que recebe a URL do usuário e exibe os links extraídos |
| **API Server** | Python (step5) ou Ruby (step6) | Serviço de extração de links exposto como API REST |
| **Cache** | Redis | Armazena resultados de extrações anteriores para acelerar respostas |

### Fluxo de funcionamento
Usuário → PHP (front-end) → API (Python ou Ruby) → Redis (cache)
↓ (cache miss)
Web externa

Ao receber uma URL, a API verifica primeiro o Redis. Se o resultado já estiver em cache (**cache hit**), ele é retornado imediatamente. Caso contrário (**cache miss**), a extração é feita diretamente na web e o resultado é armazenado no cache para requisições futuras.

---

## Ferramenta de Teste de Carga — Locust

[Locust](https://locust.io/) é uma ferramenta open-source de teste de carga definida inteiramente via código Python. Permite simular múltiplos usuários virtuais realizando requisições HTTP simultaneamente, com métricas de desempenho em tempo real.

### Scripts implementados

Dois scripts foram desenvolvidos para cobrir os cenários com e sem cache:

#### `locustfile_com_cache.py`
Simula usuários que fazem requisições normais à API, permitindo que o Redis armazene e reutilize resultados.

```python
@task
def extract_links_sequence(self):
    shuffled = URLS.copy()
    random.shuffle(shuffled)  # ordem aleatória para simular usuários reais

    for url in shuffled:
        encoded_url = url.replace("://", "%3A%2F%2F").replace("/", "%2F")
        self.client.get(f"/api/{encoded_url}", name="/api/[url]")
```

#### `locustfile_sem_cache.py`
Simula usuários que forçam bypass do cache via parâmetro `?nocache=1`, garantindo que cada requisição busque os dados diretamente na web.

```python
@task
def extract_links_sequence_no_cache(self):
    for url in shuffled:
        self.client.get(f"/api/{encoded_url}?nocache=1", name="/api/[url]?nocache=1")
```

Ambos os scripts utilizam as mesmas **10 URLs-alvo**:

https://www.python.org       https://www.wikipedia.org
https://www.github.com       https://docs.docker.com
https://redis.io             https://flask.palletsprojects.com
https://www.ruby-lang.org    https://microservices.io
https://play-with-docker.com https://hub.docker.com

Cada usuário virtual realiza **10 invocações por ciclo** em ordem aleatória, com tempo de espera de **0,5 a 1,5 segundos** entre tarefas.

---

## Cenários de Teste

Os testes variaram três dimensões:

| Dimensão | Valores |
|----------|---------|
| **Usuários virtuais** | 1, 5, 10, 25, 50, 100, ... |
| **Versão da API** | Python (step5) · Ruby (step6) |
| **Modo de cache** | Com cache (Redis) · Sem cache (bypass) |

Isso resulta em uma matriz de cenários:

Python + Com cache    × N usuários
Python + Sem cache    × N usuários
Ruby   + Com cache    × N usuários
Ruby   + Sem cache    × N usuários

---

## Como Executar

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e Docker Compose
- Python 3.8+ com Locust instalado:
```bash
  pip install locust
```

### 1. Subir a aplicação (versão Python)

```bash
cd linkextractor-master/step5
docker-compose up --build
```

A API ficará disponível em `http://localhost:5000`.

### 2. Subir a aplicação (versão Ruby)

```bash
cd linkextractor-master/step6
docker-compose up --build
```

A API ficará disponível em `http://localhost:4567`.

### 3. Executar os testes de carga

**Com cache:**
```bash
locust -f testes-locust/locustfile_com_cache.py --host http://localhost:5000
```

**Sem cache:**
```bash
locust -f testes-locust/locustfile_sem_cache.py --host http://localhost:5000
```

Acesse a interface web do Locust em `http://localhost:8089` para configurar o número de usuários e iniciar os testes.

---

## Métricas Coletadas

Para cada cenário foram registradas as seguintes métricas exportadas pelo Locust:

- **Média** do tempo de resposta
- **Mediana** (P50) do tempo de resposta
- **Percentis P90 e P95** do tempo de resposta
- **Requisições por segundo (RPS)**
- **Taxa de falhas**
