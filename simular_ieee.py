import numpy as np
import pandapower as pp
import pandapower.networks as pn
import pandas as pd

# Ajustar numero de barras do sistema para formatação correta dos arquivos de resultados
numbarras = 118
print(f"Carregando sistema IEEE {numbarras} nativo...")
# Carrega o sistema IEEE padrão (que é exatamente o que está no seu txt) IMPORTANTE: LEMBRE DE MUDAR O CASE
net = pn.case118()

print(f"Rede carregada: {len(net.bus)} barras, {len(net.line)} linhas.")


# Simular a contingência (Exemplo: abrir linha entre barra 1 e 2)
def contingencia(linha_contingencia: pd.DataFrame):
    linha_contingencia = net.line[
        (net.line.from_bus == 0) & (net.line.to_bus == 1)
    ].index

    if not linha_contingencia.empty:
        idx = linha_contingencia[0]
        print(f"\nAbrindo linha {idx} (Barra 0 -> Barra 1)...")
        net.line.at[idx, "in_service"] = False
        pp.runpp(net, algorithm="nr")
        print("Novo estado calculado.")
        return net.res_bus[["vm_pu", "va_degree", "p_mw", "q_mvar"]].head()
    else:
        print(
            "Linha específica não encontrada para contingência (verifique os índices)."
        )
        return


# Rodar o fluxo
pp.runpp(net, algorithm="nr")

# Salvar resultados
net.res_bus.index.name = "Bus"
net.res_bus.index = net.bus.index + 1

df = net.res_bus.copy()

df_out = pd.DataFrame(index=df.index)

# Tensões
df_out["VM_PU"] = df["vm_pu"]
df_out["VA_GRAU"] = df["va_degree"]

# Potência ativa
df_out["P_CARGA"] = np.where(df["p_mw"] > 0, df["p_mw"], 0.0)
df_out["P_GER"] = np.where(df["p_mw"] < 0, -df["p_mw"], 0.0)

# Potência reativa
df_out["Q_CARGA"] = np.where(df["q_mvar"] > 0, df["q_mvar"], 0.0)
df_out["Q_GER"] = np.where(df["q_mvar"] < 0, -df["q_mvar"], 0.0)

# net.res_bus[["vm_pu", "va_degree", "p_mw", "q_mvar"]].to_csv(
#    f"resultados/ieee{numbarras}_pandapower.csv", sep=";", decimal=","
# )

df_out.to_csv(f"resultados/ieee{numbarras}_pandapower.csv", sep=";", decimal=",")

print(
    f"Arquivo de resultados salvo na pasta resultados como ieee{numbarras}_pandapower.csv"
)
