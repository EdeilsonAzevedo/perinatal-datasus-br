# perinatal-datasus-br

Análises de saúde perinatal e neonatal com dados públicos do **MS/DATASUS** (SIM e SINASC).  
Desenvolvido no contexto do TCC sobre acompanhamento pós-alta de prematuros pelo Método Canguru — UFAL.

---

## Análises disponíveis

| Notebook | Descrição |
|---|---|
| [`notebooks/sobrevida_neonatal.ipynb`](notebooks/sobrevida_neonatal.ipynb) | Probabilidade acumulada de óbito infantil por grupo de prematuridade — foco em Alagoas (AL), 2022 |

## Estrutura

```
perinatal-datasus-br/
├── notebooks/          # Jupyter notebooks com análises documentadas
├── graficos/
│   ├── AL/             # Gráficos gerados para Alagoas
│   └── outros_estados/ # Gráficos gerados para os demais estados
└── scripts/            # Scripts Python auxiliares
```

## Fonte dos dados

- **SIM** — Sistema de Informações sobre Mortalidade (MS/DATASUS, 2022)
- **SINASC** — Sistema de Informações sobre Nascidos Vivos (MS/DATASUS, 2022)
- Acesso via [pysus](https://github.com/AlertaDengue/PySUS)

## Dependências

```bash
pip install pysus pandas numpy matplotlib
```

---

<sub>Dados públicos disponibilizados pelo Ministério da Saúde. Uso exclusivamente acadêmico.</sub>
