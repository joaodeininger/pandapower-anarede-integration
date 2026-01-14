import pandas as pd
import pandapower as pp
import math

def parse_pwf_to_pandapower(pwf_file_path, base_mva=100.0):
    net = pp.create_empty_network()
    
    # Dicionários para mapear numeração original -> índice pandapower
    bus_map = {} 
    
    print(f"Lendo arquivo: {pwf_file_path}")
    
    with open(pwf_file_path, 'r', encoding='latin-1') as f:
        lines = f.readlines()
    
    current_section = None
    
    # Buffers para guardar dados
    dbar_lines = []
    dlin_lines = []
    dger_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('('): continue # Pula comentários
        
        # Detecta Seção
        if line.startswith('DBAR'):
            current_section = 'DBAR'
            continue
        elif line.startswith('DLIN'):
            current_section = 'DLIN'
            continue
        elif line.startswith('DGER'):
            current_section = 'DGER'
            continue
        elif line.startswith('99999'):
            current_section = None
            continue
            
        # Adiciona linha ao buffer correto
        if current_section == 'DBAR':
            dbar_lines.append(line)
        elif current_section == 'DLIN':
            dlin_lines.append(line)
        elif current_section == 'DGER':
            dger_lines.append(line)

    print(f"  Encontrados: {len(dbar_lines)} Barras, {len(dlin_lines)} Ramos, {len(dger_lines)} Geradores")

    # ==========================================================================
    # 1. PROCESSAR BARRAS (DBAR)
    # Formato típico ANAREDE (Colunas fixas podem variar, usando split como approx)
    # ==========================================================================
    print("Processando Barras...")
    for l in dbar_lines:
        # ANAREDE é posicional, mas vamos tentar splitar por segurança
        # Colunas comuns: Num, Op, Estado, Tensao, Ang, CargaP, CargaQ, Shunt, Nome...
        # Ex: 1      1    1000 0    51.0   27.0   0.0 ...
        parts = l.split()
        
        bus_num = int(parts[0])
        # area = int(parts[2]) # As vezes
        # tensao_base = float(line[...]) # Difícil pegar sem saber a coluna exata
        # Vamos assumir Vn=138kV padrão se não tiver explícito, ou tentar inferir.
        # Para simplificar, vou assumir Vn genérico ou ler de uma tabela externa.
        vn_kv = 138.0  # <--- ATENÇÃO: Se tiver níveis diferentes, precisa lógica para detectar
        
        # Tensão inicial (Vm) e Angulo (Va)
        # Normalmente colunas: ... Vm Ang PL QL ...
        # Ajuste os índices abaixo conforme o SEU pwf (abra no bloco de notas para contar)
        # Assumindo layout padrão reduzido:
        # Num(0) Nome(?) ... PL(col X) QL(col Y)
        
        # DICA: O melhor é usar fwf (fixed width) se souber as posições. 
        # Vou usar uma lógica robusta de "procurar cargas":
        
        # Cria a barra
        pp_idx = pp.create_bus(net, vn_kv=vn_kv, name=f"Barra {bus_num}", index=bus_num-1)
        bus_map[bus_num] = pp_idx
        
        # Cargas e Shunts (Simplificado: precisa ver onde estão no seu PWF)
        # Se você tiver o CSV "118_barras_novo_2.csv", é melhor importar Cargas dele
        # pois o PWF é chato de ler colunas sem documentação rígida.
        
    # ==========================================================================
    # 2. PROCESSAR LINHAS E TRAFOS (DLIN)
    # ==========================================================================
    print("Processando Linhas e Trafos...")
    for l in dlin_lines:
        # Layout típico: De Para Circ R(%) X(%) Mvar(B) Tap(pu) ...
        parts = l.split()
        
        from_bus = int(parts[0])
        to_bus = int(parts[1])
        # O "De" e "Para" precisam existir
        if from_bus not in bus_map or to_bus not in bus_map: continue
        
        r_perc = float(parts[3])
        x_perc = float(parts[4])
        b_val = float(parts[5]) # Pode ser Mvar totais ou %
        tap = 0.0
        
        # Tenta achar Tap (geralmente coluna 6 ou 7)
        if len(parts) > 6:
            try: tap = float(parts[6])
            except: pass
            
        # Identificar se é Trafo ou Linha
        # No ANAREDE, se tem TAP definido (diferente de 0 ou 1 fixo sem controle), é trafo
        # Ou se R/X forem típicos de trafo. Mas a regra do TAP é a melhor.
        
        # Conversão de Unidades (Assumindo Base 100MVA e 138kV)
        z_base = (138.0**2) / base_mva
        r_ohm = (r_perc / 100.0) * z_base
        x_ohm = (x_perc / 100.0) * z_base
        
        # Se for Trafo
        if tap > 0 and tap != 1.0 and abs(tap - 1.0) > 0.001: 
             # Lógica de Trafo
             # Pandapower pede Sn, V_hv, V_lv, vk_percent, vkr_percent
             # Vamos criar um trafo com parâmetros "custom"
             pp.create_transformer_from_parameters(net, 
                 hv_bus=bus_map[from_bus], 
                 lv_bus=bus_map[to_bus], 
                 sn_mva=base_mva, 
                 vn_hv_kv=138.0, 
                 vn_lv_kv=138.0, # Assumindo autotrafo ou regulador na mesma base
                 vkr_percent=r_perc, 
                 vk_percent=math.sqrt(r_perc**2 + x_perc**2), 
                 pfe_kw=0, 
                 i0_percent=0,
                 tap_pos=0, # Ajuste fino depois
                 tap_neutral=0,
                 tap_step_percent=(abs(1-tap)*100) # Simplificação
             )
        else:
            # Lógica de Linha
            # B no ANAREDE geralmente é Mvar totais gerados a 1pu
            # Pandapower pede C_nf_per_km.
            # Q = V² * w * C
            # C (F) = Q / (V² * 2*pi*60)
            # Se Q está em Mvar (ex: 900 Mvar -> 900e6)
            
            # Cuidado: B_val pode ser Susceptancia em % ou Mvar. 
            # Assumindo Mvar totais ("Shunt de Linha"):
            q_mvar = b_val
            w = 2 * math.pi * 60
            v_base_si = 138.0 * 1e3
            
            if q_mvar != 0:
                c_farad = (q_mvar * 1e6) / (v_base_si**2 * w)
                c_nf = c_farad * 1e9
            else:
                c_nf = 0.0
                
            pp.create_line_from_parameters(net, 
                from_bus=bus_map[from_bus], 
                to_bus=bus_map[to_bus], 
                length_km=1.0, # Unitário para usar parametros totais
                r_ohm_per_km=r_ohm, 
                x_ohm_per_km=x_ohm, 
                c_nf_per_km=c_nf, 
                max_i_ka=1.0 # Default
            )

    # ==========================================================================
    # 3. PROCESSAR GERADORES (DGER)
    # ==========================================================================
    print("Processando Geradores...")
    for l in dger_lines:
        parts = l.split()
        bus_num = int(parts[0])
        p_gen = float(parts[1])
        q_min = float(parts[2])
        q_max = float(parts[3])
        
        # Tenta achar V_set (muitas vezes nas ultimas colunas ou coluna de controle)
        # Se não achar, usa 1.0 ou pega do DBAR
        
        if bus_num in bus_map:
            pp.create_gen(net, bus=bus_map[bus_num], p_mw=p_gen, 
                          min_q_mvar=q_min, max_q_mvar=q_max, vm_pu=1.0)

    return net

# --- COMO USAR ---
# 1. Aponte para seu arquivo PWF
# net_convertida = parse_pwf_to_pandapower("IEEE118.pwf")
# pp.runpp(net_convertida)