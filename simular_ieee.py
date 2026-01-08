import numpy as np
import pandapower as pp
import pandapower.networks as pn
import pandas as pd

# 1. Carregar IEEE 118
numbarras = 118
print(f"Processando IEEE {numbarras}...")
net = pn.case118()

# 2. Rodar Fluxo
pp.runpp(net, algorithm="nr")
print("Fluxo convergido.")

# 3. Preparar DataFrame
df_out = pd.DataFrame(index=net.bus.index)
df_out.index.name = "Bus"

# --- TENSÕES (Direto da barra) ---
df_out["VM_PU"] = net.res_bus["vm_pu"]
df_out["VA_GRAU"] = net.res_bus["va_degree"]

# --- CÁLCULO DA INJEÇÃO LÍQUIDA ---
# Inicializa Series com Zeros indexadas pelas barras
p_inj = pd.Series(0.0, index=net.bus.index)
q_inj = pd.Series(0.0, index=net.bus.index)

# --- A. GERAÇÃO (Soma P e Q injetados) ---

# 1. Slack (External Grid)
if not net.ext_grid.empty:
    # A tabela de resultados (res_ext_grid) não tem a coluna 'bus'.
    # Usamos o indice da tabela de entrada para saber qual barra é.
    # Mapeamos o resultado P para a barra correspondente.
    p_slack = net.res_ext_grid["p_mw"].groupby(net.ext_grid["bus"]).sum()
    q_slack = net.res_ext_grid["q_mvar"].groupby(net.ext_grid["bus"]).sum()

    p_inj = p_inj.add(p_slack, fill_value=0)
    q_inj = q_inj.add(q_slack, fill_value=0)

# 2. Geradores (Gen)
if not net.gen.empty:
    # Agrupa o resultado (res_gen) usando a coluna 'bus' da entrada (gen)
    p_gen = net.res_gen["p_mw"].groupby(net.gen["bus"]).sum()
    q_gen = net.res_gen["q_mvar"].groupby(net.gen["bus"]).sum()

    p_inj = p_inj.add(p_gen, fill_value=0)
    q_inj = q_inj.add(q_gen, fill_value=0)

# 3. Geradores Estáticos (Sgen)
if not net.sgen.empty:
    p_sgen = net.res_sgen["p_mw"].groupby(net.sgen["bus"]).sum()
    q_sgen = net.res_sgen["q_mvar"].groupby(net.sgen["bus"]).sum()

    p_inj = p_inj.add(p_sgen, fill_value=0)
    q_inj = q_inj.add(q_sgen, fill_value=0)

# --- B. SHUNTS (Capacitores/Reatores) ---
if not net.shunt.empty:
    # Shunts: P positivo aqui significa consumo (perda), Q positivo é injeção capacitiva?
    # No pandapower res_shunt: p_mw é consumo, q_mvar é injeção (depende da convenção).
    # Vamos somar algebricamente. Se for banco de capacitor, Q vem positivo ou negativo?
    # Geralmente, res_shunt traz o valor efetivo. Vamos somar como injeção.
    # Se o sinal estiver trocado em relação ao ANAREDE, trocaremos para .sub()
    p_shunt = net.res_shunt["p_mw"].groupby(net.shunt["bus"]).sum()
    q_shunt = net.res_shunt["q_mvar"].groupby(net.shunt["bus"]).sum()

    # Shunt geralmente é modelado como carga no fluxo, mas queremos ver o efeito líquido.
    # P de shunt é perda -> entra subtraindo (ou somando negativo)
    # Q de shunt (capacitor) -> injeta -> entra somando

    # Nota: No output padrão do pandapower, res_shunt Q é negativo para indutores e positivo para capacitores?
    # Melhor assumir soma algébrica da injeção.
    p_inj = p_inj.add(p_shunt, fill_value=0)
    q_inj = p_inj.add(q_shunt, fill_value=0)

# --- C. CARGAS (Subtrai P e Q consumidos) ---
if not net.load.empty:
    p_load = net.res_load["p_mw"].groupby(net.load["bus"]).sum()
    q_load = net.res_load["q_mvar"].groupby(net.load["bus"]).sum()

    p_inj = p_inj.sub(p_load, fill_value=0)
    q_inj = q_inj.sub(q_load, fill_value=0)


# --- FORMATAR PARA O CSV ---
# Saldo > 0 -> Geração Líquida
# Saldo < 0 -> Carga Líquida

df_out["P_GER_LIQ"] = p_inj.apply(lambda x: x if x > 1e-5 else 0)
df_out["P_CARGA_LIQ"] = p_inj.apply(lambda x: abs(x) if x < -1e-5 else 0)

df_out["Q_GER_LIQ"] = q_inj.apply(lambda x: x if x > 1e-5 else 0)
df_out["Q_CARGA_LIQ"] = q_inj.apply(lambda x: abs(x) if x < -1e-5 else 0)

# Ajuste Index (de 0-based para 1-based se necessário)
df_out.index = df_out.index + 1
df_out = df_out.round(4)

df_out.to_csv(f"resultados/ieee{numbarras}_liquido_corrigido_v2.csv", sep=";", decimal=",")
print("Concluído e salvo.")
