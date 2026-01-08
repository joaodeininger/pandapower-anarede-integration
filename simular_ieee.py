import numpy as np
import pandapower as pp
import pandapower.networks as pn
import pandas as pd

# 1. Configuração e Carregamento
numbarras = 118
print(f"Carregando sistema IEEE {numbarras} nativo...")
net = pn.case118()

# 2. Rodar o Fluxo de Potência
pp.runpp(net, algorithm="nr")
print("Fluxo de potência convergido.")

# 3. Criação do DataFrame final (Indexado pelo número da barra)
# Usamos o índice original das barras (0 a 13) para agrupar, depois somamos 1 para virar ID ANAREDE
df_out = pd.DataFrame(index=net.bus.index)
df_out.index.name = "Bus"

# --- A. TENSÕES E ÂNGULOS (Vêm direto do resultado da barra) ---
df_out["VM_PU"] = net.res_bus["vm_pu"]
df_out["VA_GRAU"] = net.res_bus["va_degree"]

# --- B. CARGAS (Vêm da tabela de input de Carga) ---
# Agrupamos as cargas pelo ID da barra, pois pode haver mais de uma carga por barra
# fill_value=0 garante que barras sem carga fiquem com 0 e não NaN
df_out["P_CARGA"] = net.load.groupby("bus")["p_mw"].sum()
df_out["Q_CARGA"] = net.load.groupby("bus")["q_mvar"].sum()

# --- C. GERAÇÃO (Vem de TRÊS lugares diferentes) ---
# No Pandapower, geração vem de:
# 1. ext_grid (Slack)
# 2. gen (Geradores PV)
# 3. sgen (Geradores estáticos - opcional, mas bom ter)

# Inicializa colunas de geração com 0
df_out["P_GER"] = 0.0
df_out["Q_GER"] = 0.0

# C.1 Adicionar Slack (External Grid) - IMPORTANTE: Usar res_ext_grid (pois a potência é calculada)
# Mapeia o resultado do slack para a barra onde ele está conectado
if not net.ext_grid.empty:
    slack_bus_ids = net.ext_grid["bus"]
    # .values para alinhar corretamente caso os indices não batam direto
    df_out.loc[slack_bus_ids, "P_GER"] += net.res_ext_grid["p_mw"].values
    df_out.loc[slack_bus_ids, "Q_GER"] += net.res_ext_grid["q_mvar"].values

# C.2 Adicionar Geradores (Gen) - Usar res_gen para pegar o valor exato (especialmente Q)
if not net.gen.empty:
    # Agrupa resultados dos geradores por barra
    p_gen_by_bus = net.res_gen.groupby(net.gen["bus"])["p_mw"].sum()
    q_gen_by_bus = net.res_gen.groupby(net.gen["bus"])["q_mvar"].sum()

    # Soma ao dataframe existente (usando add para preservar o que já veio do Slack)
    df_out["P_GER"] = df_out["P_GER"].add(p_gen_by_bus, fill_value=0)
    df_out["Q_GER"] = df_out["Q_GER"].add(q_gen_by_bus, fill_value=0)

# C.3 Adicionar Geradores Estáticos (sgen) - caso existam
if not net.sgen.empty:
    p_sgen_by_bus = net.res_sgen.groupby(net.sgen["bus"])["p_mw"].sum()
    q_sgen_by_bus = net.res_sgen.groupby(net.sgen["bus"])["q_mvar"].sum()

    df_out["P_GER"] = df_out["P_GER"].add(p_sgen_by_bus, fill_value=0)
    df_out["Q_GER"] = df_out["Q_GER"].add(q_sgen_by_bus, fill_value=0)

# 4. Limpeza e Formatação Final
df_out = df_out.fillna(0.0)  # Remove NaNs remanescentes

# Ajustar índice para começar de 1 (Padrão ANAREDE/IEEE)
df_out.index = df_out.index + 1

# Arredondamento opcional para ficar bonito
df_out = df_out.round(4)

# Salvar
file_name = f"resultados/ieee{numbarras}_pandapower.csv"
df_out.to_csv(file_name, sep=";", decimal=",")

print(f"Arquivo salvo com sucesso: {file_name}")
print("\n--- Amostra das Barras com Geração e Carga (Ex: Barra 2) ---")
print(df_out.loc[[1, 2, 3]])  # Mostra barras 1, 2 e 3 para conferência
