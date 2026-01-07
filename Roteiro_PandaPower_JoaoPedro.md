# PDF: Roteiro de Estudo - PandaPower (João Pedro)
**Foco:** Programação e Flexibilidade

---

## Referências Úteis (Documentação Oficial):
- [PandaPower Documentation (Read the Docs)](https://pandapower.readthedocs.io/)
- [PandaPower Tutorials (GitHub)](https://github.com/e2nIEE/pandapower/tree/master/tutorials)

---

---

## 1. Preparação do Ambiente:

1. **Instalação:**
   - Instalar o Python.
   - Instalar a biblioteca: `pip install pandapower`.

2. **Ponto de Partida (Código):**
   ```python
   import pandapower as pp
   import pandas as pd
   net = pp.create_empty_network()
   ```

---

## 2. Fluxo de Tarefas (Sistema Padrão de 5 Barras):

### Tabela Técnica de Referência
Siga estes parâmetros exatamente para permitir a comparação posterior com o ANAREDE:

**Barras:**
- Barra 1: Swing (Slack), V=1.05 pu, θ=0°.
- Barra 2: PQ, Carga P=50MW, Q=20MVAr.
- Barra 3: PV, Geração P=60MW, V=1.02 pu.
- Barra 4: PQ, Carga P=40MW, Q=15MVAr.
- Barra 5: PQ, Carga P=30MW, Q=10MVAr.

**Linhas (Base 100MVA, 138kV):**
| Trajeto | R (pu/km) | X (pu/km) | B (pu/km) | Comprimento (km) |
| :--- | :--- | :--- | :--- | :--- |
| L1-2 | 0.02 | 0.06 | 0.04 | 10 |
| L2-3 | 0.03 | 0.09 | 0.06 | 20 |
| L3-4 | 0.02 | 0.06 | 0.04 | 15 |
| L4-5 | 0.04 | 0.12 | 0.08 | 10 |
| L5-1 | 0.01 | 0.03 | 0.02 | 25 |

1. **Modelagem:** Criar o script com as 5 barras e linhas descritas.
2. **Execução:** Usar `pp.runpp(net, algorithm='nr')`.
3. **Contingência:** Simular abertura da linha L1-2 e registrar impactos.

---

## 3. Saída e Comparação:
1. Gerar DataFrame com: **Tensão (pu)**, **Ângulo (graus)**, **P (MW)** e **Q (MVAr)**.
2. Exportar para `.csv`.
3. **Comparar os resultados com o relatório gerado no ANAREDE (Victor Quirino).**

---

## Integração Final: Visualizando a Aplicação
Após concluir as atividades técnicas acima, siga estes passos para ver seu trabalho integrado ao projeto:
1. Abra o **Terminal** ou **PowerShell**.
2. Execute o comando: `git clone https://github.com/TenProject/Front_dev.git`
3. Entre na pasta: `cd Front_dev`
