import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re

PASTA_RESULTADOS = Path("resultados")
PASTA_GRAFICOS = Path("graficos")

PASTA_GRAFICOS.mkdir(exist_ok=True)


def identificar_cenario(nome_arquivo):
    """
    Identifica linguagem, cache e quantidade de usuários pelo nome do arquivo.

    Exemplos aceitos:
    python_com_cache_10.csv
    python_sem_cache_50.csv
    ruby_com_cache_100.csv
    ruby_sem_cache_100.csv
    """

    nome = nome_arquivo.lower()

    padrao = r"(python|ruby)_(com_cache|sem_cache)_(\d+)\.csv"
    resultado = re.search(padrao, nome)

    if not resultado:
        return None

    linguagem = resultado.group(1).capitalize()
    cache = "Com cache" if resultado.group(2) == "com_cache" else "Sem cache"
    usuarios = int(resultado.group(3))

    return linguagem, cache, usuarios


def pegar_coluna(df, opcoes):
    """
    Tenta encontrar uma coluna no CSV mesmo que o nome varie um pouco.
    """

    for coluna in opcoes:
        if coluna in df.columns:
            return coluna

    return None


def ler_csv_locust(caminho_csv):
    """
    Lê um CSV do Locust e pega a linha Aggregated.
    Se não encontrar Aggregated, pega a última linha.
    """

    df = pd.read_csv(caminho_csv)

    if "Name" in df.columns:
        linha_aggregated = df[df["Name"].astype(str).str.lower() == "aggregated"]
    else:
        linha_aggregated = pd.DataFrame()

    if linha_aggregated.empty:
        linha = df.iloc[-1]
    else:
        linha = linha_aggregated.iloc[0]

    coluna_requests = pegar_coluna(df, ["Request Count", "# Requests"])
    coluna_falhas = pegar_coluna(df, ["Failure Count", "# Fails"])
    coluna_mediana = pegar_coluna(df, ["Median Response Time", "Median"])
    coluna_media = pegar_coluna(df, ["Average Response Time", "Average"])
    coluna_minimo = pegar_coluna(df, ["Min Response Time", "Min"])
    coluna_maximo = pegar_coluna(df, ["Max Response Time", "Max"])
    coluna_rps = pegar_coluna(df, ["Requests/s", "Current RPS"])
    coluna_p90 = pegar_coluna(df, ["90%", "90%ile"])
    coluna_p95 = pegar_coluna(df, ["95%", "95%ile"])
    coluna_p99 = pegar_coluna(df, ["99%", "99%ile"])

    return {
        "Requests": linha[coluna_requests] if coluna_requests else 0,
        "Falhas": linha[coluna_falhas] if coluna_falhas else 0,
        "Mediana": linha[coluna_mediana] if coluna_mediana else 0,
        "Media": linha[coluna_media] if coluna_media else 0,
        "Minimo": linha[coluna_minimo] if coluna_minimo else 0,
        "Maximo": linha[coluna_maximo] if coluna_maximo else 0,
        "RPS": linha[coluna_rps] if coluna_rps else 0,
        "P90": linha[coluna_p90] if coluna_p90 else 0,
        "P95": linha[coluna_p95] if coluna_p95 else 0,
        "P99": linha[coluna_p99] if coluna_p99 else 0,
    }



# LEITURA DOS RESULTADOS

dados = []

arquivos_csv = list(PASTA_RESULTADOS.glob("*.csv"))

if not arquivos_csv:
    print("Nenhum CSV encontrado na pasta 'resultados'.")
    print("Coloque os arquivos .csv dentro da pasta resultados e rode novamente.")
    exit()

for arquivo in arquivos_csv:
    cenario = identificar_cenario(arquivo.name)

    if cenario is None:
        print(f"Ignorando arquivo com nome fora do padrão: {arquivo.name}")
        continue

    linguagem, cache, usuarios = cenario
    metricas = ler_csv_locust(arquivo)

    dados.append({
        "Versao API": linguagem,
        "Cache": cache,
        "Usuarios": usuarios,
        **metricas
    })

df = pd.DataFrame(dados)

if df.empty:
    print("Nenhum dado válido foi encontrado.")
    exit()

df = df.sort_values(["Cache", "Versao API", "Usuarios"])

df.to_csv("resumo_resultados.csv", index=False)

print("\nResumo dos resultados:")
print(df)

print("\nArquivo 'resumo_resultados.csv' gerado com sucesso.")



# FUNÇÕES PARA GERAR GRÁFICOS

def gerar_grafico_comparativo_colunas(metrica, titulo, eixo_y, nome_arquivo):
    """
    Gráfico comparativo geral em colunas.

    Comparação:
    - Python com cache
    - Python sem cache
    - Ruby com cache
    - Ruby sem cache

    Esse gráfico substitui os antigos gráficos de linha.
    """

    df_temp = df.copy()

    df_temp["Cenario"] = df_temp["Versao API"] + " - " + df_temp["Cache"]

    tabela = df_temp.pivot(
        index="Usuarios",
        columns="Cenario",
        values=metrica
    )

    tabela = tabela.sort_index()

    ordem_colunas = [
        "Python - Com cache",
        "Python - Sem cache",
        "Ruby - Com cache",
        "Ruby - Sem cache"
    ]

    colunas_existentes = [col for col in ordem_colunas if col in tabela.columns]
    tabela = tabela[colunas_existentes]

    ax = tabela.plot(
        kind="bar",
        figsize=(11, 6),
        width=0.8,
        title=titulo
    )

    ax.set_xlabel("Quantidade de usuários virtuais")
    ax.set_ylabel(eixo_y)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.legend(title="Cenário")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(PASTA_GRAFICOS / nome_arquivo)
    plt.close()

    print(f"Gráfico gerado: {PASTA_GRAFICOS / nome_arquivo}")


def gerar_grafico_python_vs_ruby_por_cache(cache, metrica, titulo, eixo_y, nome_arquivo):
    """
    Gera gráfico de colunas comparando Python vs Ruby
    dentro de um modo de cache específico.

    Exemplo:
    - Python vs Ruby com cache
    - Python vs Ruby sem cache
    """

    df_cache = df[df["Cache"] == cache]

    if df_cache.empty:
        print(f"Nenhum dado encontrado para: {cache}")
        return

    tabela = df_cache.pivot(
        index="Usuarios",
        columns="Versao API",
        values=metrica
    )

    tabela = tabela.sort_index()

    ordem_colunas = ["Python", "Ruby"]
    colunas_existentes = [col for col in ordem_colunas if col in tabela.columns]
    tabela = tabela[colunas_existentes]

    ax = tabela.plot(
        kind="bar",
        figsize=(10, 6),
        width=0.8,
        title=titulo
    )

    ax.set_xlabel("Quantidade de usuários virtuais")
    ax.set_ylabel(eixo_y)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.legend(title="Versão da API")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(PASTA_GRAFICOS / nome_arquivo)
    plt.close()

    print(f"Gráfico gerado: {PASTA_GRAFICOS / nome_arquivo}")



# GRÁFICOS COMPARATIVOS GERAIS EM COLUNAS

gerar_grafico_comparativo_colunas(
    metrica="Media",
    titulo="Comparativo geral: tempo médio de resposta",
    eixo_y="Tempo médio de resposta (ms)",
    nome_arquivo="comparativo_colunas_media.png"
)

gerar_grafico_comparativo_colunas(
    metrica="Mediana",
    titulo="Comparativo geral: tempo mediano de resposta",
    eixo_y="Tempo mediano de resposta (ms)",
    nome_arquivo="comparativo_colunas_mediana.png"
)

gerar_grafico_comparativo_colunas(
    metrica="P95",
    titulo="Comparativo geral: percentil 95 do tempo de resposta",
    eixo_y="Percentil 95 (ms)",
    nome_arquivo="comparativo_colunas_p95.png"
)

gerar_grafico_comparativo_colunas(
    metrica="RPS",
    titulo="Comparativo geral: requisições por segundo",
    eixo_y="Requisições por segundo (RPS)",
    nome_arquivo="comparativo_colunas_rps.png"
)

gerar_grafico_comparativo_colunas(
    metrica="Falhas",
    titulo="Comparativo geral: falhas por cenário",
    eixo_y="Quantidade de falhas",
    nome_arquivo="comparativo_colunas_falhas.png"
)



# GRÁFICOS PYTHON VS RUBY COM CACHE

gerar_grafico_python_vs_ruby_por_cache(
    cache="Com cache",
    metrica="Media",
    titulo="Com cache: tempo médio de resposta - Python vs Ruby",
    eixo_y="Tempo médio de resposta (ms)",
    nome_arquivo="com_cache_media_python_vs_ruby.png"
)

gerar_grafico_python_vs_ruby_por_cache(
    cache="Com cache",
    metrica="Mediana",
    titulo="Com cache: tempo mediano de resposta - Python vs Ruby",
    eixo_y="Tempo mediano de resposta (ms)",
    nome_arquivo="com_cache_mediana_python_vs_ruby.png"
)

gerar_grafico_python_vs_ruby_por_cache(
    cache="Com cache",
    metrica="P95",
    titulo="Com cache: percentil 95 - Python vs Ruby",
    eixo_y="Percentil 95 (ms)",
    nome_arquivo="com_cache_p95_python_vs_ruby.png"
)

gerar_grafico_python_vs_ruby_por_cache(
    cache="Com cache",
    metrica="RPS",
    titulo="Com cache: requisições por segundo - Python vs Ruby",
    eixo_y="Requisições por segundo (RPS)",
    nome_arquivo="com_cache_rps_python_vs_ruby.png"
)



# GRÁFICOS PYTHON VS RUBY SEM CACHE

gerar_grafico_python_vs_ruby_por_cache(
    cache="Sem cache",
    metrica="Media",
    titulo="Sem cache: tempo médio de resposta - Python vs Ruby",
    eixo_y="Tempo médio de resposta (ms)",
    nome_arquivo="sem_cache_media_python_vs_ruby.png"
)

gerar_grafico_python_vs_ruby_por_cache(
    cache="Sem cache",
    metrica="Mediana",
    titulo="Sem cache: tempo mediano de resposta - Python vs Ruby",
    eixo_y="Tempo mediano de resposta (ms)",
    nome_arquivo="sem_cache_mediana_python_vs_ruby.png"
)

gerar_grafico_python_vs_ruby_por_cache(
    cache="Sem cache",
    metrica="P95",
    titulo="Sem cache: percentil 95 - Python vs Ruby",
    eixo_y="Percentil 95 (ms)",
    nome_arquivo="sem_cache_p95_python_vs_ruby.png"
)

gerar_grafico_python_vs_ruby_por_cache(
    cache="Sem cache",
    metrica="RPS",
    titulo="Sem cache: requisições por segundo - Python vs Ruby",
    eixo_y="Requisições por segundo (RPS)",
    nome_arquivo="sem_cache_rps_python_vs_ruby.png"
)



print("\n--- CONCLUÍDO ---")
print("Gráficos gerados na pasta 'graficos'.")
print("Resumo geral salvo em 'resumo_resultados.csv'.")