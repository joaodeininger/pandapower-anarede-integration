from pandapower.create import (
    create_bus,
    create_empty_network,
    create_ext_grid,
    create_gen,
    create_load
)
from pandapower.create.line_create import create_line_from_parameters
from pandapower.run import runpp
from pu_to_unit import add_line

# Base Tension Value given in Table
V_base_kv = 138

net = create_empty_network()

# Bus Creation
bus1 = create_bus(net, vn_kv=V_base_kv, name="Bus 1")
bus2 = create_bus(net, vn_kv=V_base_kv, name="Bus 2")
bus3 = create_bus(net, vn_kv=V_base_kv, name="Bus 3")
bus4 = create_bus(net, vn_kv=V_base_kv, name="Bus 4")
bus5 = create_bus(net, vn_kv=V_base_kv, name="Bus 5")

# Bus Elements
create_ext_grid(net, bus=bus1, vm_pu=1.05, name="Swing Slack")
create_load(net, bus=bus2, p_mw=50, q_mvar=20, name="Load1")
create_gen(net, bus=bus3, p_mw=60, vm_pu=1.02, name="Generator")
create_load(net, bus=bus4, p_mw=40, q_mvar=15, name="Load2")
create_load(net, bus=bus5, p_mw=30, q_mvar=10, name="Load3")

# Line Creation
# Calls add_line, which converts parameters from pu_km to the pandapower unit
line1_2 = add_line(0.0010, 0.0025, 0.0005, 10)
line2_3 = add_line(0.0010, 0.0025, 0.0005, 20)
line3_4 = add_line(0.0010, 0.0025, 0.0005, 15)
line4_5 = add_line(0.0010, 0.0025, 0.0005, 10)
line5_1 = add_line(0.0010, 0.0025, 0.0005, 25)

# Line creation using add_line() parameters
create_line_from_parameters(
    net,
    from_bus=bus1,
    to_bus=bus2,
    r_ohm_per_km=line1_2[0],
    x_ohm_per_km=line1_2[1],
    c_nf_per_km=line1_2[2],
    length_km=line1_2[3],
    max_i_ka=100,
    name="line1-2",
)

create_line_from_parameters(
    net,
    from_bus=bus2,
    to_bus=bus3,
    r_ohm_per_km=line2_3[0],
    x_ohm_per_km=line2_3[1],
    c_nf_per_km=line2_3[2],
    length_km=line2_3[3],
    max_i_ka=100,
    name="line2-3",
)
create_line_from_parameters(
    net,
    from_bus=bus3,
    to_bus=bus4,
    r_ohm_per_km=line3_4[0],
    x_ohm_per_km=line3_4[1],
    c_nf_per_km=line3_4[2],
    length_km=line3_4[3],
    max_i_ka=100,
    name="line3-4",
)
create_line_from_parameters(
    net,
    from_bus=bus4,
    to_bus=bus5,
    r_ohm_per_km=line4_5[0],
    x_ohm_per_km=line4_5[1],
    c_nf_per_km=line4_5[2],
    length_km=line4_5[3],
    max_i_ka=100,
    name="line4-5",
)
create_line_from_parameters(
    net,
    from_bus=bus5,
    to_bus=bus1,
    r_ohm_per_km=line5_1[0],
    x_ohm_per_km=line5_1[1],
    c_nf_per_km=line5_1[2],
    length_km=line5_1[3],
    max_i_ka=100,
    name="line5-1",
)

# Execution
runpp(net, algorithm="nr")

# Results and export
results = net.res_bus[["vm_pu", "va_degree"]].copy()
results["P_mw"] = net.res_bus["p_mw"]
results["Q_mvar"] = net.res_bus["q_mvar"]

print("\nResultados das Barras:")
print(results)

results.to_csv("resultados/resultados_pandapower_joaopedro.csv")
print("\nResultados exportados para 'resultados/resultados_pandapower_joaopedro.csv'")

# Contingency simulation
print("\n--- Simulação de Contingência: Abrindo line1-2 ---")

# Open line1-2
net.line.loc[net.line.name == "line1-2", "in_service"] = False

runpp(net, algorithm="nr")

print("Resultados Pós-Contingência (Tensões nas Barras):")
print(net.res_bus[["vm_pu", "va_degree"]])

net.res_bus.to_csv("resultados/resultados_pandapower_joaopedro_contingencia.csv")
print("\nResultados da contingência salvos em 'resultados/resultados_pandapower_joaopedro_contingencia.csv'")
