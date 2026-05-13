import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re


# CONFIGURAÇÕES

PASTA_RESULTADOS = Path("resultados")
PASTA_GRAFICOS = Path("graficos")

PASTA_GRAFICOS.mkdir(exist_ok=True)


# FUNÇÕES AUXILIARES

def identificar_cenario(nome_arquivo):
    """
    Identifica linguagem, cache e quantidade de usuários pelo nome do arquivo.

    Exemplos aceitos:
    python_com_cache_10.csv
    python_sem_cache_100.csv
    ruby_com_cache_50.csv
    ruby_sem_cache_100.csv
    """

    nome = nome_arquivo.lower()

    padrao = r"(python|ruby)_(com_cache|sem_cache)_(\d+)\.csv"
    resultado = re.search(padrao, nome)

    if not resultado:
        return None

    linguagem = resultado.group(1).capitalize()
    cache = "Sim" if resultado.group(2) == "com_cache" else "Não"
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

    linha_aggregated = df[df["Name"].astype(str).str.lower() == "aggregated"]

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
        "Versão API": linguagem,
        "Cache Ligado?": cache,
        "Usuários": usuarios,
        **metricas
    })

df = pd.DataFrame(dados)

if df.empty:
    print("Nenhum dado válido foi encontrado.")
    exit()

df = df.sort_values(["Versão API", "Cache Ligado?", "Usuários"])

# Salva um resumo geral em CSV
df.to_csv("resumo_resultados.csv", index=False)

print("\nResumo dos resultados:")
print(df)

print("\nArquivo 'resumo_resultados.csv' gerado com sucesso.")



# FUNÇÕES PARA GERAR GRÁFICOS

def gerar_grafico_por_versao(versao_api, metrica, titulo, eixo_y, nome_arquivo):
    """
    Gera gráfico de barras comparando com cache e sem cache
    para uma versão específica: Python ou Ruby.
    """

    df_versao = df[df["Versão API"] == versao_api]

    if df_versao.empty:
        print(f"Nenhum dado encontrado para {versao_api}.")
        return

    tabela = df_versao.pivot(
        index="Usuários",
        columns="Cache Ligado?",
        values=metrica
    )

    tabela = tabela.sort_index()

    ax = tabela.plot(
        kind="bar",
        figsize=(10, 6),
        width=0.8,
        title=titulo
    )

    ax.set_xlabel("Quantidade de usuários virtuais")
    ax.set_ylabel(eixo_y)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.legend(title="Cache ativo?")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(PASTA_GRAFICOS / nome_arquivo)
    plt.close()

    print(f"Gráfico gerado: {PASTA_GRAFICOS / nome_arquivo}")


def gerar_grafico_comparativo(metrica, titulo, eixo_y, nome_arquivo):
    """
    Gera gráfico de linhas comparando:
    Python com cache, Python sem cache, Ruby com cache e Ruby sem cache.
    """

    plt.figure(figsize=(10, 6))

    for linguagem in ["Python", "Ruby"]:
        for cache in ["Sim", "Não"]:
            filtro = df[
                (df["Versão API"] == linguagem) &
                (df["Cache Ligado?"] == cache)
            ].sort_values("Usuários")

            if filtro.empty:
                continue

            label_cache = "com cache" if cache == "Sim" else "sem cache"
            label = f"{linguagem} - {label_cache}"

            plt.plot(
                filtro["Usuários"],
                filtro[metrica],
                marker="o",
                label=label
            )

    plt.title(titulo)
    plt.xlabel("Quantidade de usuários virtuais")
    plt.ylabel(eixo_y)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(PASTA_GRAFICOS / nome_arquivo)
    plt.close()

    print(f"Gráfico gerado: {PASTA_GRAFICOS / nome_arquivo}")



# GRÁFICOS POR VERSÃO

for versao in ["Python", "Ruby"]:

    gerar_grafico_por_versao(
        versao_api=versao,
        metrica="Mediana",
        titulo=f"{versao}: tempo mediano de resposta",
        eixo_y="Tempo mediano de resposta (ms)",
        nome_arquivo=f"grafico_mediana_{versao.lower()}.png"
    )

    gerar_grafico_por_versao(
        versao_api=versao,
        metrica="Media",
        titulo=f"{versao}: tempo médio de resposta",
        eixo_y="Tempo médio de resposta (ms)",
        nome_arquivo=f"grafico_media_{versao.lower()}.png"
    )

    gerar_grafico_por_versao(
        versao_api=versao,
        metrica="P95",
        titulo=f"{versao}: percentil 95 do tempo de resposta",
        eixo_y="Percentil 95 (ms)",
        nome_arquivo=f"grafico_p95_{versao.lower()}.png"
    )

    gerar_grafico_por_versao(
        versao_api=versao,
        metrica="RPS",
        titulo=f"{versao}: requisições por segundo",
        eixo_y="Requisições por segundo (RPS)",
        nome_arquivo=f"grafico_rps_{versao.lower()}.png"
    )

    gerar_grafico_por_versao(
        versao_api=versao,
        metrica="Falhas",
        titulo=f"{versao}: quantidade de falhas",
        eixo_y="Quantidade de falhas",
        nome_arquivo=f"grafico_falhas_{versao.lower()}.png"
    )



# GRÁFICOS COMPARATIVOS GERAIS

gerar_grafico_comparativo(
    metrica="Mediana",
    titulo="Comparativo geral: tempo mediano de resposta",
    eixo_y="Tempo mediano de resposta (ms)",
    nome_arquivo="comparativo_mediana.png"
)

gerar_grafico_comparativo(
    metrica="Media",
    titulo="Comparativo geral: tempo médio de resposta",
    eixo_y="Tempo médio de resposta (ms)",
    nome_arquivo="comparativo_media.png"
)

gerar_grafico_comparativo(
    metrica="P95",
    titulo="Comparativo geral: percentil 95 do tempo de resposta",
    eixo_y="Percentil 95 (ms)",
    nome_arquivo="comparativo_p95.png"
)

gerar_grafico_comparativo(
    metrica="RPS",
    titulo="Comparativo geral: requisições por segundo",
    eixo_y="Requisições por segundo (RPS)",
    nome_arquivo="comparativo_rps.png"
)

gerar_grafico_comparativo(
    metrica="Falhas",
    titulo="Comparativo geral: falhas por cenário",
    eixo_y="Quantidade de falhas",
    nome_arquivo="comparativo_falhas.png"
)



# FINALIZAÇÃO

print("\n--- CONCLUÍDO ---")
print("Gráficos gerados na pasta 'graficos'.")
print("Resumo geral salvo em 'resumo_resultados.csv'.")