import pandapower as pp
import pandapower.networks as pn

# Ajustar numero de barras do sistema para formatação correta dos arquivos de resultados
numbarras = 57
print(f"Carregando sistema IEEE {numbarras} nativo...")
# Carrega o sistema IEEE padrão (que é exatamente o que está no seu txt) IMPORTANTE: LEMBRE DE MUDAR O CASE
net = pn.case57()

print(f"Rede carregada: {len(net.bus)} barras, {len(net.line)} linhas.")

# Rodar o fluxo
pp.runpp(net, algorithm="nr")

# Mostrar resultados
print(f"\n--- Resultados (IEEE {numbarras}) ---")
print(net.res_bus[["vm_pu", "va_degree", "p_mw", "q_mvar"]])
net.res_bus[["vm_pu", "va_degree"]].to_csv(
    f"resultados_ieee{numbarras}.csv", index=False
)

# Simular a contingência (Exemplo: abrir linha entre barra 1 e 2)
# No case14, os índices das barras começam em 0 ou 1 dependendo da versão,
# vamos buscar pelo nome ou pelos índices de conexão.
linha_contingencia = net.line[(net.line.from_bus == 0) & (net.line.to_bus == 1)].index

if not linha_contingencia.empty:
    idx = linha_contingencia[0]
    print(f"\nAbrindo linha {idx} (Barra 0 -> Barra 1)...")
    net.line.at[idx, "in_service"] = False
    pp.runpp(net, algorithm="nr")
    print("Novo estado calculado.")
    print(net.res_bus[["vm_pu", "va_degree", "p_mw", "q_mvar"]].head())
else:
    print("Linha específica não encontrada para contingência (verifique os índices).")
