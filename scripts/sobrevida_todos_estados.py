"""
Análise de Sobrevida Neonatal por Estado — Brasil 2022
Gera um gráfico por UF com probabilidade acumulada de óbito
por grupo de prematuridade (SIM × SINASC 2022)

Fonte: MS/DATASUS — SIM e SINASC 2022
Autor: TCC Karu / UFAL

Saída: graficos_sobrevida_2022/<UF>_sobrevida_neonatal_2022.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────

ANO   = 2022
PASTA = 'graficos_sobrevida_2022'
os.makedirs(PASTA, exist_ok=True)

ESTADOS = [
    'AC','AL','AM','AP','BA','CE','DF','ES','GO',
    'MA','MG','MS','MT','PA','PB','PE','PI','PR',
    'RJ','RN','RO','RR','RS','SC','SE','SP','TO'
]

# Paleta visual
TEAL   = '#0d9488'
SLATE  = '#334155'
RED    = '#e11d48'
AMBER  = '#f59e0b'
GRAY   = '#94a3b8'
LIGHT  = '#f1f5f9'
PURPLE = '#7c3aed'

GRUPOS_ORDEM = [
    'Extremamente\nprematuro\n(<28 sem)',
    'Muito\nprematuro\n(28–31 sem)',
    'Prematuro\ntardio\n(32–36 sem)',
    'A termo\n(37–41 sem)',
]

COR_GRUPO = {
    'Extremamente\nprematuro\n(<28 sem)': RED,
    'Muito\nprematuro\n(28–31 sem)':      AMBER,
    'Prematuro\ntardio\n(32–36 sem)':     PURPLE,
    'A termo\n(37–41 sem)':               TEAL,
}

JANELAS = {
    'Até\n24h':      1,
    'Até\n1 semana': 7,
    'Até\n1 mês':    28,
    'Até\n3 meses':  90,
    'Até\n6 meses':  180,
}

plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor':   LIGHT,
    'axes.edgecolor':   SLATE,
    'axes.labelcolor':  SLATE,
    'axes.titlesize':   13,
    'axes.titleweight': 'bold',
    'axes.titlecolor':  SLATE,
    'xtick.color':      SLATE,
    'ytick.color':      SLATE,
    'grid.color':       'white',
    'grid.linewidth':   1.2,
    'font.family':      'sans-serif',
    'text.color':       SLATE,
})


# ─────────────────────────────────────────────
# FUNÇÕES
# ─────────────────────────────────────────────

def classifica_grupo(gest):
    if pd.isna(gest):
        return None
    try:
        gest = int(gest)
    except:
        return None
    if gest in [1, 2]: return 'Extremamente\nprematuro\n(<28 sem)'
    if gest == 3:       return 'Muito\nprematuro\n(28–31 sem)'
    if gest == 4:       return 'Prematuro\ntardio\n(32–36 sem)'
    if gest == 5:       return 'A termo\n(37–41 sem)'
    return None


def prep_sim(df_raw, col_gestacao='GESTACAO'):
    """Prepara o SIM: filtra óbitos infantis e classifica grupos."""
    df = df_raw.copy()
    df['DTOBITO'] = pd.to_datetime(df['DTOBITO'], format='%d%m%Y', errors='coerce')
    df['DTNASC']  = pd.to_datetime(df['DTNASC'],  format='%d%m%Y', errors='coerce')
    df['IDADE_DIAS'] = (df['DTOBITO'] - df['DTNASC']).dt.days

    # óbitos não-fetais
    if 'TIPOBITO' in df.columns:
        df = df[df['TIPOBITO'] == '2']

    # óbitos infantis < 1 ano
    df = df[df['IDADE_DIAS'].between(0, 364)].copy()
    df['GESTACAO_N'] = pd.to_numeric(df[col_gestacao], errors='coerce')
    df['GRUPO'] = df['GESTACAO_N'].apply(classifica_grupo)
    return df


def prep_sinasc(df_raw):
    """Prepara o SINASC: detecta coluna de gestação e classifica grupos."""
    df = df_raw.copy()
    # detectar nome da coluna de gestação
    col = None
    for candidato in ['GESTACAO', 'SEMAGESTAC', 'GRAVIDEZ']:
        if candidato in df.columns:
            col = candidato
            break
    if col is None:
        print(f"  AVISO: coluna de gestação não encontrada. Colunas: {df.columns.tolist()}")
        return None, None
    df['GESTACAO_N'] = pd.to_numeric(df[col], errors='coerce')
    # se for SEMAGESTAC (semanas diretas), converter para faixas
    if col == 'SEMAGESTAC':
        def sem_para_faixa(s):
            if pd.isna(s): return None
            s = int(s)
            if s < 22:  return 1
            if s < 28:  return 2
            if s < 32:  return 3
            if s < 37:  return 4
            if s < 42:  return 5
            return 6
        df['GESTACAO_N'] = df['GESTACAO_N'].apply(sem_para_faixa)
    df['GRUPO'] = df['GESTACAO_N'].apply(classifica_grupo)
    return df, col


def calcula_probabilidades(df_inf, denominadores):
    """Calcula matriz de probabilidades acumuladas."""
    resultados = {}
    df_clean = df_inf[df_inf['GRUPO'].notna()].copy()
    for grupo in GRUPOS_ORDEM:
        resultados[grupo] = {}
        n_nascidos = denominadores.get(grupo, 0)
        df_grupo   = df_clean[df_clean['GRUPO'] == grupo]
        for janela_label, limite_dias in JANELAS.items():
            n_mortos = (df_grupo['IDADE_DIAS'] < limite_dias).sum()
            prob = (n_mortos / n_nascidos * 100) if n_nascidos > 0 else 0
            resultados[grupo][janela_label] = round(prob, 2)
    return resultados


def gera_grafico(uf, resultados, denominadores, ano):
    """Gera e salva o gráfico para uma UF."""
    janelas_labels = list(JANELAS.keys())
    n_janelas = len(janelas_labels)
    n_grupos  = len(GRUPOS_ORDEM)
    width = 0.18
    x = np.arange(n_janelas)

    fig, ax = plt.subplots(figsize=(14, 7))

    for i, grupo in enumerate(GRUPOS_ORDEM):
        valores  = [resultados[grupo][j] for j in janelas_labels]
        posicoes = x + (i - n_grupos / 2 + 0.5) * width
        cor      = COR_GRUPO[grupo]
        bars = ax.bar(posicoes, valores, width=width * 0.92,
                      color=cor, zorder=2, alpha=0.92)
        for bar, val in zip(bars, valores):
            if val >= 0.05:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.05,
                    f'{val:.1f}%',
                    ha='center', va='bottom',
                    fontsize=7.5, color=SLATE, fontweight='bold'
                )

    ax.set_xticks(x)
    ax.set_xticklabels(janelas_labels, fontsize=11)
    ax.set_ylabel('Probabilidade acumulada de óbito (%)', fontsize=11)
    ax.set_xlabel('Janela de sobrevida (acumulado desde o nascimento)', fontsize=10)
    ax.set_title(
        f'Probabilidade Acumulada de Óbito Infantil por Grupo de Prematuridade\n'
        f'{uf} — {ano}  |  Fonte: SIM × SINASC / MS-DATASUS',
        fontsize=13, pad=15
    )
    ax.yaxis.grid(True, zorder=1, alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
    ylim_max = max(
        max(resultados[g][j] for j in janelas_labels)
        for g in GRUPOS_ORDEM
    )
    ax.set_ylim(0, max(ylim_max * 1.2, 1))

    handles = []
    for grupo in GRUPOS_ORDEM:
        n = denominadores.get(grupo, 0)
        nome_curto = grupo.replace('\n', ' ')
        handles.append(mpatches.Patch(
            color=COR_GRUPO[grupo],
            label=f'{nome_curto}  (n={n:,} nascidos)'
        ))
    ax.legend(handles=handles, loc='upper left',
              framealpha=0.95, fontsize=9.5,
              title='Grupo gestacional', title_fontsize=10)

    fig.text(
        0.99, 0.01,
        'Nota: excluídos óbitos com gestação ignorada ou pós-termo (≥42 sem).\n'
        'Denominador = nascidos vivos (SINASC). Numerador = óbitos infantis (SIM).',
        ha='right', va='bottom', fontsize=7.5, color=GRAY, style='italic'
    )

    plt.tight_layout()
    nome_arquivo = os.path.join(PASTA, f'{uf}_sobrevida_neonatal_{ano}.png')
    plt.savefig(nome_arquivo, dpi=150, bbox_inches='tight')
    plt.close()
    return nome_arquivo


# ─────────────────────────────────────────────
# LOOP PRINCIPAL — um gráfico por estado
# ─────────────────────────────────────────────

from pysus import sim, sinasc

erros   = []
sucesso = []

for uf in ESTADOS:
    print(f"\n{'─'*40}")
    print(f"Processando {uf}...")

    try:
        # 1. Baixar dados
        df_sim_raw  = sim(state=uf,    year=ANO)
        df_nasc_raw = sinasc(state=uf, year=ANO)

        if df_sim_raw is None or len(df_sim_raw) == 0:
            print(f"  AVISO: SIM vazio para {uf}")
            erros.append((uf, 'SIM vazio'))
            continue

        if df_nasc_raw is None or len(df_nasc_raw) == 0:
            print(f"  AVISO: SINASC vazio para {uf}")
            erros.append((uf, 'SINASC vazio'))
            continue

        # 2. Preparar SIM
        df_inf = prep_sim(df_sim_raw)
        print(f"  Óbitos infantis: {len(df_inf)}")

        # 3. Preparar SINASC
        df_nasc, col_gest = prep_sinasc(df_nasc_raw)
        if df_nasc is None:
            erros.append((uf, 'coluna gestação não encontrada no SINASC'))
            continue
        print(f"  Nascidos vivos: {len(df_nasc)} (coluna gestação: {col_gest})")

        # 4. Denominadores
        denominadores = df_nasc['GRUPO'].value_counts()

        # 5. Calcular probabilidades
        resultados = calcula_probabilidades(df_inf, denominadores)

        # 6. Gerar e salvar gráfico
        caminho = gera_grafico(uf, resultados, denominadores, ANO)
        print(f"  Salvo: {caminho}")
        sucesso.append(uf)

    except Exception as e:
        print(f"  ERRO em {uf}: {e}")
        erros.append((uf, str(e)))

# ─────────────────────────────────────────────
# RESUMO FINAL
# ─────────────────────────────────────────────
print(f"\n{'='*40}")
print(f"CONCLUÍDO")
print(f"  Gerados com sucesso: {len(sucesso)} estados → {sucesso}")
print(f"  Com erro:            {len(erros)}")
for uf, motivo in erros:
    print(f"    {uf}: {motivo}")
print(f"\nGráficos salvos em: ./{PASTA}/")