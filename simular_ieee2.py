import numpy as np
import pandapower as pp
import pandapower.networks as pn
import pandas as pd

# 1. Carregar IEEE 118 padrão
print("Carregando caso IEEE 118...")
net = pn.case118()

# -------------------------------------------------------------------------
# AJUSTE IMPORTANTE: Limites de Reativos
# O ANAREDE costuma travar o Q nos limites. O Pandapower padrão não.
# Ao ativar isso, aproximamos o comportamento (PV vira PQ se estourar limite).
# -------------------------------------------------------------------------
print("Executando fluxo de potência (Considerando limites de Q)...")
try:
    pp.runpp(net, algorithm="nr", enforce_q_lims=True, calculate_voltage_angles=True)
except pp.LoadflowNotConverged:
    print("AVISO: Convergência estrita falhou. Tentando sem limites de Q...")
    pp.runpp(net, algorithm="nr", enforce_q_lims=False)

print("Fluxo convergido.")

# 3. Estruturar DataFrame de Saída
# Criamos um DataFrame base com todas as barras (1 a 118)
df_out = pd.DataFrame(index=net.bus.index)
df_out.index.name = "Bus_ID"

# Coluna Identificadora
df_out["Numero"] = df_out.index

# --- A. TENSÃO E ÂNGULO ---
df_out["Tensao (p.u.)"] = net.res_bus["vm_pu"]
df_out["Angulo (graus)"] = net.res_bus["va_degree"]

# --- B. CARGAS (LOAD) ---
# Inicializa com 0.0
df_out["Carga Ativa (MW)"] = 0.0
df_out["Carga Reativa (Mvar)"] = 0.0

if not net.load.empty:
    # Agrupa por barra e soma (caso haja mais de uma carga na mesma barra)
    p_load = net.res_load["p_mw"].groupby(net.load["bus"]).sum()
    q_load = net.res_load["q_mvar"].groupby(net.load["bus"]).sum()
    
    df_out.loc[p_load.index, "Carga Ativa (MW)"] = p_load
    df_out.loc[q_load.index, "Carga Reativa (Mvar)"] = q_load

# --- C. GERAÇÃO (GEN + EXT_GRID + SGEN) ---
# Aqui somamos todas as fontes que injetam potência
df_out["Geracao Ativa (MW)"] = 0.0
df_out["Geracao Reativa (Mvar)"] = 0.0

# Series temporárias
p_gen_total = pd.Series(0.0, index=net.bus.index)
q_gen_total = pd.Series(0.0, index=net.bus.index)

# C.1 Slack (External Grid)
if not net.ext_grid.empty:
    p_slack = net.res_ext_grid["p_mw"].groupby(net.ext_grid["bus"]).sum()
    q_slack = net.res_ext_grid["q_mvar"].groupby(net.ext_grid["bus"]).sum()
    p_gen_total = p_gen_total.add(p_slack, fill_value=0)
    q_gen_total = q_gen_total.add(q_slack, fill_value=0)

# C.2 Geradores Convencionais (Gen)
if not net.gen.empty:
    p_gen = net.res_gen["p_mw"].groupby(net.gen["bus"]).sum()
    q_gen = net.res_gen["q_mvar"].groupby(net.gen["bus"]).sum()
    p_gen_total = p_gen_total.add(p_gen, fill_value=0)
    q_gen_total = q_gen_total.add(q_gen, fill_value=0)

# C.3 Geradores Estáticos / Renováveis (Sgen)
if not net.sgen.empty:
    p_sgen = net.res_sgen["p_mw"].groupby(net.sgen["bus"]).sum()
    q_sgen = net.res_sgen["q_mvar"].groupby(net.sgen["bus"]).sum()
    p_gen_total = p_gen_total.add(p_sgen, fill_value=0)
    q_gen_total = q_gen_total.add(q_sgen, fill_value=0)

df_out["Geracao Ativa (MW)"] = p_gen_total
df_out["Geracao Reativa (Mvar)"] = q_gen_total

# --- D. SHUNT ---
# No Pandapower, Shunt é tratado como impedância constante.
# res_shunt['q_mvar'] é positivo se consome (indutor) e negativo se injeta (capacitor),
# MAS o ANAREDE geralmente mostra Capacitor como positivo na injeção ou negativo na carga.
# Vamos seguir a lógica: Injeção Líquida do Shunt = - (Valor do PP)
df_out["Shunt (Mvar)"] = 0.0

if not net.shunt.empty:
    # q_mvar do pandapower: >0 Consome (Indutor), <0 Injeta (Capacitor)
    q_shunt_val = net.res_shunt["q_mvar"].groupby(net.shunt["bus"]).sum()
    
    # Inverter sinal para representar Injeção (padrão comum de relatórios de fluxo)
    # Se ANAREDE mostra reatores (consumo) como negativo, mantenha a inversão:
    # PP(Indutor)=10 -> -10 (Injeção negativa)
    df_out.loc[q_shunt_val.index, "Shunt (Mvar)"] = -1 * q_shunt_val

# --- E. COLUNAS EXTRAS (Para match perfeito com ANAREDE) ---
cols_extras = [
    "Nome", "Potencia Ativa Elo DC (MW)", "Potencia Reativa Elo DC (Mvar)",
    "Injecao Equivalente (MW)", "Injecao Equivalente (Mvar)", 
    "Motor de Inducao (MW)", "Motor de Inducao (Mvar)"
]
for col in cols_extras:
    df_out[col] = 0.0

# --- F. REORDENAR E SALVAR ---
# Ordem exata do seu CSV de exemplo
cols_order = [
    "Numero", "Tensao (p.u.)", "Angulo (graus)", 
    "Carga Ativa (MW)", "Carga Reativa (Mvar)", 
    "Geracao Ativa (MW)", "Geracao Reativa (Mvar)", 
    "Shunt (Mvar)"
]
df_final = df_out[cols_order]

output_file = "resultados/ieee118_pandapower.csv"
print(f"Salvando CSV formatado em: {output_file}")

df_final.to_csv(
    output_file,
    sep=";",
    decimal=",",
    index=False,
    float_format="%.2f"
)
print("Concluído!")