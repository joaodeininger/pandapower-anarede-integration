import numpy as np

# Define here the initial parameters, before using the function
V_base_kV = 138
S_base_mVA = 100
Z_base = V_base_kV**2 / S_base_mVA
freq = 60


def add_line(r_pu, x_pu, b_pu, length_km):
    # Conversão de Resistência e Reatância
    r_ohm_per_km = r_pu * Z_base
    x_ohm_per_km = x_pu * Z_base

    # Conversão de Susceptância (B) para Capacitância (C)
    # B_siemens = B_pu / Z_base
    # B = 2 * pi * f * C  => C = B / (2 * pi * f)
    b_siemens_per_km = b_pu / Z_base
    c_farad_per_km = b_siemens_per_km / (2 * np.pi * freq)
    c_nf_per_km = c_farad_per_km * 1e9  # Converte para nanoFarads

    data = np.array([r_ohm_per_km, x_ohm_per_km, c_nf_per_km, length_km])
    return data
