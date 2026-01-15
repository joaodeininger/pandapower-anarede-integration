import pandapower as pp
import math
import pandas as pd

# Ajuste o caminho do arquivo aqui
arquivo = "ieee/118_barras_relatorio_DBAR_DLIN.txt"
output_file = "convs/saida_118_barras.csv"

def parse_anarede_final(txt_file):
    net = pp.create_empty_network()
    bus_lookup = {}
    mode = None

    print(f"--- Lendo Relatório: {txt_file} ---")
    with open(txt_file, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split()
        if not parts: continue

        # --- DETECÇÃO DE SEÇÃO ---
        if "DADOS DE BARRA" in line: mode = 'BUS'; continue
        if "DADOS DE LINHA" in line or "DADOS DE CIRCUITO" in line: mode = 'LINE'; continue
        
        # Filtro: Ignora linhas que não começam com número (Cabeçalhos)
        if not parts[0].isdigit(): continue

        try:
            # ==================================================================
            # 1. LEITURA DE BARRAS (Mantida a versão robusta anterior)
            # ==================================================================
            if mode == 'BUS':
                num = int(parts[0])
                tipo = int(parts[2]) # 2=Slack, 1=PV, 0=PQ
                
                idx = pp.create_bus(net, vn_kv=138.0, name=parts[1], index=num-1)
                bus_lookup[num] = idx
                
                # Posições fixas (Tensão/Angulo) e Relativas (Carga/Shunt)
                v_pu = float(parts[5])
                ang = float(parts[6])
                net.bus.at[idx, 'vm_pu'] = v_pu
                net.bus.at[idx, 'va_degree'] = ang

                shunt = float(parts[-2]) # Penúltimo
                ql = float(parts[-3])
                pl = float(parts[-4])
                pg = float(parts[11])
                qmin = float(parts[12])
                qmax = float(parts[14])

                if pl != 0 or ql != 0:
                    pp.create_load(net, bus=idx, p_mw=pl, q_mvar=ql)
                
                if shunt != 0:
                    # Invertendo sinal: Se ANAREDE mostra (+), PP entende (-) como cap
                    pp.create_shunt(net, bus=idx, q_mvar=-shunt, p_mw=0)

                if tipo == 2: # Slack
                    pp.create_ext_grid(net, bus=idx, vm_pu=v_pu, va_degree=ang,
                                       min_q_mvar=qmin, max_q_mvar=qmax)
                elif tipo == 1 or pg > 0: # PV
                    pp.create_gen(net, bus=idx, p_mw=pg, vm_pu=v_pu, 
                                  min_q_mvar=qmin, max_q_mvar=qmax)

            # ==================================================================
            # 2. LEITURA DE LINHAS E TRAFOS (Lógica Simplificada)
            # ==================================================================
            elif mode == 'LINE':
                if len(parts) < 8: continue
                
                de = int(parts[0])
                para = int(parts[1])
                
                if de not in bus_lookup or para not in bus_lookup: continue

                # EXTRAIR APENAS OS NÚMEROS (Floats) APÓS O "DE/PARA"
                # Isso ignora "Lig", "Desl", nomes, etc.
                # Sequência esperada de floats: [NC, Area, R, X, B, (TAP?), Limite...]
                
                floats = []
                for p in parts[2:]:
                    try: floats.append(float(p))
                    except: pass
                
                # Precisamos de pelo menos R, X, B (índices 2, 3, 4 na lista de floats)
                # Índice 0 é NC (Num Circuito), Índice 1 é Area (geralmente)
                if len(floats) < 5: continue 
                
                r_perc = floats[2]
                x_perc = floats[3]
                b_mvar = floats[4]
                
                # VERIFICAÇÃO SIMPLES DE TAP:
                # O número logo após o B (índice 5) é o TAP se existir e for pequeno.
                tap = 1.0
                is_trafo = False
                
                if len(floats) > 5:
                    prox_valor = floats[5]
                    # Se o valor for menor que 2.0 (ex: 0.978), é Tap. 
                    # Se for > 2.0 (ex: 500.0, 9999.0), é Limite de fluxo.
                    if prox_valor < 2.0:
                        tap = prox_valor
                        is_trafo = True
                        # Se R=0 e X>0 e tem Tap, com certeza é trafo.

                # CONVERSÕES
                z_base = (138.0**2) / 100.0
                
                if is_trafo:
                    # --- É TRANSFORMADOR ---
                    # Calcula Z em %
                    z_perc = math.sqrt(r_perc**2 + x_perc**2)
                    if z_perc == 0: z_perc = 0.1 # Evita divisão por zero
                    
                    # Aplica o Tap na Tensão Nominal do Primário (HV)
                    # Isso simula a relação de transformação real
                    vn_hv_ajustada = 138.0 * tap
                    
                    pp.create_transformer_from_parameters(net, 
                        hv_bus=bus_lookup[de], lv_bus=bus_lookup[para], 
                        sn_mva=100.0, 
                        vn_hv_kv=vn_hv_ajustada, # Tap aplicado aqui
                        vn_lv_kv=138.0, 
                        vkr_percent=r_perc, 
                        vk_percent=z_perc, 
                        pfe_kw=0, i0_percent=0,
                        tap_pos=0, tap_neutral=0, tap_step_percent=0,
                        name=f"Trafo {de}-{para}")
                else:
                    # --- É LINHA DE TRANSMISSÃO ---
                    r_ohm = (r_perc / 100.0) * z_base
                    x_ohm = (x_perc / 100.0) * z_base
                    w = 2 * math.pi * 60
                    c_nf = (b_mvar / 100.0) * 1e9 / (w * z_base)

                    pp.create_line_from_parameters(net, 
                        from_bus=bus_lookup[de], to_bus=bus_lookup[para],
                        length_km=1.0, 
                        r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm, c_nf_per_km=c_nf, 
                        max_i_ka=2.0,
                        name=f"Linha {de}-{para}")

        except Exception as e:
            print(f"Aviso: Erro ao ler linha {parts}: {e}")

    return net

# ==============================================================================
# EXECUÇÃO E EXPORTAÇÃO
# ==============================================================================
if __name__ == "__main__":
    net = parse_anarede_final(arquivo)
    
    print(f"\nRede carregada: {len(net.bus)} barras, {len(net.trafo)} transformadores.")
    
    # Rodar Fluxo (NR) com limites de reativo
    pp.runpp(net, algorithm='nr', enforce_q_lims=True)
    print(">>> Fluxo Convergiu!")

    # Montar DataFrame de Saída
    df_out = pd.DataFrame(index=net.bus.index)
    df_out["Numero"] = df_out.index + 1
    df_out["Tensao (p.u.)"] = net.res_bus["vm_pu"]
    df_out["Angulo (graus)"] = net.res_bus["va_degree"]
    
    # Cargas
    p_load = net.res_load.groupby(net.load.bus).p_mw.sum()
    q_load = net.res_load.groupby(net.load.bus).q_mvar.sum()
    df_out["Carga Ativa (MW)"] = p_load.reindex(net.bus.index, fill_value=0.0)
    df_out["Carga Reativa (Mvar)"] = q_load.reindex(net.bus.index, fill_value=0.0)

    # Geração Total (Gen + ExtGrid)
    p_gen = pd.Series(0.0, index=net.bus.index)
    q_gen = pd.Series(0.0, index=net.bus.index)
    
    if not net.gen.empty:
        p_gen = p_gen.add(net.res_gen.groupby(net.gen.bus).p_mw.sum(), fill_value=0)
        q_gen = q_gen.add(net.res_gen.groupby(net.gen.bus).q_mvar.sum(), fill_value=0)
    if not net.ext_grid.empty:
        p_gen = p_gen.add(net.res_ext_grid.groupby(net.ext_grid.bus).p_mw.sum(), fill_value=0)
        q_gen = q_gen.add(net.res_ext_grid.groupby(net.ext_grid.bus).q_mvar.sum(), fill_value=0)

    df_out["Geracao Ativa (MW)"] = p_gen
    df_out["Geracao Reativa (Mvar)"] = q_gen

    # Shunt (Invertendo sinal para padrão de injeção se necessário)
    q_shunt = net.res_shunt.groupby(net.shunt.bus).q_mvar.sum()
    df_out["Shunt (Mvar)"] = -1 * q_shunt.reindex(net.bus.index, fill_value=0.0)

    # Exportar
    cols = ["Numero", "Tensao (p.u.)", "Angulo (graus)", 
            "Carga Ativa (MW)", "Carga Reativa (Mvar)", 
            "Geracao Ativa (MW)", "Geracao Reativa (Mvar)", "Shunt (Mvar)"]
    
    df_out[cols].to_csv(output_file, sep=";", decimal=",", index=False, float_format="%.2f")
    print(f"\nArquivo salvo: {output_file}")
    print(df_out[cols].head())