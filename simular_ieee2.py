import numpy as np
import pandapower as pp
import pandapower.networks as pn
import pandas as pd

# 1. Carregar IEEE 118
print("Carregando caso IEEE 118...")
net = pn.case118()

# 2. Rodar Fluxo de Potência (Newton-Raphson)
try:
    pp.runpp(net, algorithm="nr", enforce_q_lims=True, calculate_voltage_angles=True)
except pp.LoadflowNotConverged:
    print("Atenção: O fluxo não convergiu com limites de Q estritos.")
    print("Tentando rodar sem limites para obter uma solução aproximada...")
    pp.runpp(net, algorithm="nr", enforce_q_lims=False)

print("Fluxo convergido.")

# 3. Preparar DataFrame com base nas barras
# O índice do DataFrame será o ID da barra (1 a 118)
df_out = pd.DataFrame(index=net.bus.index)
df_out.index.name = "Bus_ID"

# Adiciona a coluna 'Numero' igual ao ANAREDE (assumindo que o index já é o número da barra)
df_out["Numero"] = df_out.index

# --- A. TENSÃO E ÂNGULO ---
# Mapeando: 'Tensao (p.u.)' e 'Angulo (graus)'
df_out["Tensao (p.u.)"] = net.res_bus["vm_pu"]
df_out["Angulo (graus)"] = net.res_bus["va_degree"]

# --- B. CARGAS (LOAD) ---
# Inicializa com zero
df_out["Carga Ativa (MW)"] = 0.0
df_out["Carga Reativa (Mvar)"] = 0.0

if not net.load.empty:
    # Agrupa resultados de carga por barra
    p_load = net.res_load["p_mw"].groupby(net.load["bus"]).sum()
    q_load = net.res_load["q_mvar"].groupby(net.load["bus"]).sum()
    
    # Preenche no DataFrame
    df_out.loc[p_load.index, "Carga Ativa (MW)"] = p_load
    df_out.loc[q_load.index, "Carga Reativa (Mvar)"] = q_load

# --- C. GERAÇÃO (GEN + EXT_GRID + SGEN) ---
# Inicializa com zero
df_out["Geracao Ativa (MW)"] = 0.0
df_out["Geracao Reativa (Mvar)"] = 0.0

# Series temporárias para somar todas as fontes de geração
p_gen_total = pd.Series(0.0, index=net.bus.index)
q_gen_total = pd.Series(0.0, index=net.bus.index)

# 1. External Grid (Slack)
if not net.ext_grid.empty:
    p_slack = net.res_ext_grid["p_mw"].groupby(net.ext_grid["bus"]).sum()
    q_slack = net.res_ext_grid["q_mvar"].groupby(net.ext_grid["bus"]).sum()
    p_gen_total = p_gen_total.add(p_slack, fill_value=0)
    q_gen_total = q_gen_total.add(q_slack, fill_value=0)

# 2. Geradores (Gen)
if not net.gen.empty:
    p_gen = net.res_gen["p_mw"].groupby(net.gen["bus"]).sum()
    q_gen = net.res_gen["q_mvar"].groupby(net.gen["bus"]).sum()
    p_gen_total = p_gen_total.add(p_gen, fill_value=0)
    q_gen_total = q_gen_total.add(q_gen, fill_value=0)

# 3. Geradores Estáticos (Sgen) - caso existam
if not net.sgen.empty:
    p_sgen = net.res_sgen["p_mw"].groupby(net.sgen["bus"]).sum()
    q_sgen = net.res_sgen["q_mvar"].groupby(net.sgen["bus"]).sum()
    p_gen_total = p_gen_total.add(p_sgen, fill_value=0)
    q_gen_total = q_gen_total.add(q_sgen, fill_value=0)

df_out["Geracao Ativa (MW)"] = p_gen_total
df_out["Geracao Reativa (Mvar)"] = q_gen_total

# --- D. SHUNT ---
# ANAREDE geralmente mostra injeção líquida do shunt.
# Pandapower 'res_shunt' mostra CONSUMO (q_mvar).
# Para alinhar (Reator = negativo no ANAREDE), multiplicamos o consumo do PP por -1.
df_out["Shunt (Mvar)"] = 0.0

if not net.shunt.empty:
    # Q de shunt no pandapower (positivo consome)
    q_shunt_cons = net.res_shunt["q_mvar"].groupby(net.shunt["bus"]).sum()
    # Converter para visão de injeção (Injeção = -Consumo)
    q_shunt_inj = -1 * q_shunt_cons
    df_out.loc[q_shunt_inj.index, "Shunt (Mvar)"] = q_shunt_inj

# --- E. COLUNAS ADICIONAIS (Para manter o formato exato do CSV, preenchemos com 0) ---
colunas_anarede_extras = [
    "Nome", "Potencia Ativa Elo DC (MW)", "Potencia Reativa Elo DC (Mvar)",
    "Injecao Equivalente (MW)", "Injecao Equivalente (Mvar)", 
    "Motor de Inducao (MW)", "Motor de Inducao (Mvar)"
]
for col in colunas_anarede_extras:
    df_out[col] = 0.0  # Ou string vazia para 'Nome' se preferir

# Reordenar colunas para ficar igual ao ANAREDE (Principais)
cols_order = [
    "Numero", "Tensao (p.u.)", "Angulo (graus)", 
    "Carga Ativa (MW)", "Carga Reativa (Mvar)", 
    "Geracao Ativa (MW)", "Geracao Reativa (Mvar)", 
    "Shunt (Mvar)"
]
# Seleciona apenas as colunas de interesse para exportação limpa
df_final = df_out[cols_order]

# 4. Exportar para CSV
output_file = "ieee118_comparacao_anarede.csv"
print(f"Salvando arquivo: {output_file}")

# Configuração para formato brasileiro (ponto e vírgula, decimal com vírgula)
df_final.to_csv(
    output_file,
    sep=";",
    decimal=",",
    index=False,
    float_format="%.2f"
)

print("Concluído.")