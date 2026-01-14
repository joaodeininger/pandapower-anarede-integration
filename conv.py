



###    NÁO FUNCIONAL!! ESTOU TRABALHANDO PARA QUE FUNCIONE CORRETAMENTE###



import pandapower as pp
import pandas as pd
import math
import os

# 1. FUNÇÕES AUXILIARES DE LEITURA (BLINDADAS)
def ler_valor(linha, inicio, fim, escala=1.0, padrao=0.0):
    """Lê float de string formatada, tratando .5, -.5, vazios, etc."""
    texto = linha[inicio:fim].strip()
    if not texto or texto == ".": return padrao
    if texto.startswith('.'): texto = "0" + texto
    if texto.startswith('-.'): texto = "-0" + texto.replace('-', '')
    try:
        return float(texto) * escala
    except ValueError:
        return padrao

def ler_int(linha, inicio, fim, padrao=0):
    """Lê inteiro, retornando padrão se der erro (ex: letras onde deveria ter número)."""
    try:
        texto = linha[inicio:fim].strip()
        if not texto: return padrao
        return int(texto)
    except ValueError:
        return padrao

# 2. PARSER PWF -> PANDAPOWER
def pwf_to_pandapower(pwf_file):
    net = pp.create_empty_network()
    bus_map = {} 
    
    print(f"--- Lendo arquivo: {pwf_file} ---")
    
    # Tenta codificações comuns no Brasil
    try:
        with open(pwf_file, 'r', encoding='latin-1') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(pwf_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
    secao = None
    
    for line in lines:
        line_clean = line.strip().upper()
        
        # --- DETECÇÃO DE SEÇÃO ---
        if line_clean.startswith('DBAR'): 
            secao = 'DBAR'
            continue
        elif line_clean.startswith('DLIN'): 
            secao = 'DLIN'
            continue
        elif line_clean.startswith('DCTE') or line_clean.startswith('TITU'):
            secao = 'IGNORE'
            continue
        
        # O 99999 só encerra se já tivermos passado pelo DLIN ou se for fim real
        if line_clean.startswith('99999'): 
            if secao == 'DLIN': 
                break 
            secao = None
            continue
        
        if line.startswith('(') or len(line) < 10: continue

        # --- PROCESSAR BARRAS (DBAR) ---
        if secao == 'DBAR':
            try:
                num = ler_int(line, 0, 5)
                if num == 0: continue

                # Tenta ler o tipo. Se falhar (ex: 'L1'), assume 0 (PQ)
                tipo = ler_int(line, 7, 8, padrao=0) 
                
                nome = line[10:22].strip()
                if not nome: nome = f"Barra {num}"

                v_val = ler_valor(line, 23, 28)
                # Ajuste se tensão vier em kV ou pu (heurística)
                v_pu = v_val if v_val < 2.0 else v_val * 0.001
                if v_pu < 0.1: v_pu = 1.0 # Proteção
                
                ang = ler_valor(line, 28, 32)
                
                pg = ler_valor(line, 32, 37)
                qg = ler_valor(line, 37, 42)
                qmin = ler_valor(line, 42, 47)
                qmax = ler_valor(line, 47, 52)
                
                pl = ler_valor(line, 58, 63)
                ql = ler_valor(line, 63, 68)
                shunt = ler_valor(line, 68, 73)

                # Criar Barra
                idx = pp.create_bus(net, vn_kv=138.0, name=nome, index=num-1)
                bus_map[num] = idx
                
                net.bus.at[idx, 'vm_pu'] = v_pu
                net.bus.at[idx, 'va_degree'] = ang
                
                # Carga
                if pl != 0 or ql != 0:
                    pp.create_load(net, bus=idx, p_mw=pl, q_mvar=ql)
                
                # Shunt
                if shunt != 0:
                    pp.create_shunt(net, bus=idx, q_mvar=-shunt, p_mw=0)
                    
                # Geradores (PV ou Slack)
                if tipo == 2: # Slack explícita
                    pp.create_ext_grid(net, bus=idx, vm_pu=v_pu, va_degree=ang,
                                       min_q_mvar=qmin, max_q_mvar=qmax)
                elif pg > 0 or tipo == 1: # PV
                    pp.create_gen(net, bus=idx, p_mw=pg, vm_pu=v_pu,
                                  min_q_mvar=qmin, max_q_mvar=qmax)

            except Exception as e:
                pass # Ignora linhas mal formadas

        # --- PROCESSAR RAMOS (DLIN) ---
        elif secao == 'DLIN':
            try:
                de = ler_int(line, 0, 5)
                para = ler_int(line, 10, 15)
                
                if de not in bus_map or para not in bus_map: continue
                
                r_perc = ler_valor(line, 20, 26)
                x_perc = ler_valor(line, 26, 32)
                b_ch = ler_valor(line, 32, 38)
                tap = ler_valor(line, 38, 43)
                
                idx_de = bus_map[de]
                idx_para = bus_map[para]
                
                z_base = (138.0**2) / 100.0
                r_ohm = (r_perc / 100.0) * z_base
                x_ohm = (x_perc / 100.0) * z_base
                
                if abs(tap) > 0.001:
                    vk = math.sqrt(r_perc**2 + x_perc**2)
                    if vk < r_perc: vk = r_perc + 0.01
                    if vk < 0.001: vk = 0.1

                    pp.create_transformer_from_parameters(net, 
                        hv_bus=idx_de, lv_bus=idx_para, 
                        sn_mva=100.0, vn_hv_kv=138.0, vn_lv_kv=138.0,
                        vkr_percent=r_perc, vk_percent=vk, pfe_kw=0, i0_percent=0,
                        tap_pos=-1, tap_neutral=0, tap_step_percent=(1.0-tap)*100, tap_side='hv')
                else:
                    c_nf = 0
                    if b_ch != 0:
                        w = 2 * math.pi * 60
                        c_farad = (b_ch * 1e6) / ((138000**2) * w)
                        c_nf = c_farad * 1e9
                    
                    pp.create_line_from_parameters(net,
                        from_bus=idx_de, to_bus=idx_para, length_km=1.0,
                        r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm, c_nf_per_km=c_nf,
                        max_i_ka=10.0) # Limite térmico alto para evitar erro
            except:
                pass

    return net

# 3. EXTRAÇÃO DE RESULTADOS (AGRUPADO POR BARRA)
def extrair_resultados_completos(net):
    """Gera um DataFrame consolidado por barra (Carga, Geração, Tensão)."""
    
    # 1. Base: Todas as barras
    df = pd.DataFrame(index=net.bus.index)
    df.index.name = "ID Barra"
    df["Nome"] = net.bus.name
    df["Tensao (p.u.)"] = net.res_bus.vm_pu
    df["Angulo (graus)"] = net.res_bus.va_degree
    
    # 2. Agrupar Cargas (Soma por barra)
    if not net.load.empty:
        df["Carga Ativa (MW)"] = net.res_load.groupby(net.load.bus).p_mw.sum()
        df["Carga Reativa (Mvar)"] = net.res_load.groupby(net.load.bus).q_mvar.sum()
    
    # 3. Agrupar Geração (PV + Slack)
    gen_p = pd.Series(0.0, index=net.bus.index)
    gen_q = pd.Series(0.0, index=net.bus.index)
    
    if not net.gen.empty:
        gen_p = gen_p.add(net.res_gen.groupby(net.gen.bus).p_mw.sum(), fill_value=0)
        gen_q = gen_q.add(net.res_gen.groupby(net.gen.bus).q_mvar.sum(), fill_value=0)
        
    if not net.ext_grid.empty:
        gen_p = gen_p.add(net.res_ext_grid.groupby(net.ext_grid.bus).p_mw.sum(), fill_value=0)
        gen_q = gen_q.add(net.res_ext_grid.groupby(net.ext_grid.bus).q_mvar.sum(), fill_value=0)
        
    df["Geracao Ativa (MW)"] = gen_p
    df["Geracao Reativa (Mvar)"] = gen_q
    
    # 4. Shunts
    if not net.shunt.empty:
        df["Shunt (Mvar)"] = net.res_shunt.groupby(net.shunt.bus).q_mvar.sum()

    # Limpeza
    return df.fillna(0.0).round(4)

# 4. EXECUÇÃO PRINCIPAL
if __name__ == "__main__":
    
    # --- CAMINHO DO ARQUIVO (EDITE AQUI) ---
    arquivo_pwf = "ieee/IEEE118.pwf" 
    
    if not os.path.exists(arquivo_pwf):
        print(f"ERRO: Arquivo não encontrado em {arquivo_pwf}")
    else:
        # 1. Carregar Rede
        net = pwf_to_pandapower(arquivo_pwf)
        
        # Validação de Segurança (Evita o erro de max() iterable)
        if len(net.bus) == 0:
            print("ERRO CRÍTICO: Nenhuma barra foi criada. Verifique o cabeçalho do arquivo.")
        else:
            print(f"Rede carregada: {len(net.bus)} barras.")
            
            # Garantir Slack (Fallback para barra 69 ou 0 se não houver slack)
            if len(net.ext_grid) == 0:
                print("AVISO: Adicionando Slack automática na Barra 69 (ou 1).")
                idx_slack = net.bus.index[68] if 68 in net.bus.index else net.bus.index[0]
                pp.create_ext_grid(net, bus=idx_slack, vm_pu=1.0, va_degree=0)

            # 2. Rodar Fluxo (Flat Start para melhor convergência)
            try:
                pp.runpp(net, algorithm='nr', init_vm_pu="flat", calculate_voltage_angles=True)
                print(">>> CONVERGIU!")
                
                # 3. Extrair Resultados
                df_res = extrair_resultados_completos(net)
                
                # Exibir no Console
                print("\n--- Resultados (Primeiras 10 Barras) ---")
                print(df_res.head(10))
                
                # 4. Salvar em CSV (Compatível com Anarede)
                saida_csv = "resultado_pandapower.csv"
                df_res.to_csv(saida_csv, sep=';', decimal=',')
                print(f"\nRelatório completo salvo em: {saida_csv}")
                
            except Exception as e:
                print(f"Erro no Fluxo de Potência: {e}")