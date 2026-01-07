import pandas as pd


def converter_para_float(serie):
    """
    Tenta converter uma coluna para float, lidando com vírgulas e erros.
    """
    # 1. Se já for numérico, retorna direto
    if pd.api.types.is_numeric_dtype(serie):
        return serie

    # 2. Converte para string para poder manipular
    serie = serie.astype(str)

    # 3. Substitui vírgula por ponto (Correção para padrão BR)
    serie = serie.str.replace(",", ".")

    # 4. Converte para número.
    # errors='coerce' transforma textos inválidos (ex: "N/A") em NaN (Not a Number) em vez de travar
    return pd.to_numeric(serie, errors="coerce")


def calcular_erro_percentual(arquivo_x, arquivo_y, col_x, col_y, barras):
    """
    Carrega dois CSVs e calcula o erro percentual entre duas colunas.

    Parâmetros:
    - arquivo_x: Caminho para o CSV do programa X (Referência)
    - arquivo_y: Caminho para o CSV do programa Y
    - col_x: Nome da coluna de dados no arquivo X
    - col_y: Nome da coluna de dados no arquivo Y
    - col_chave: (Opcional) Nome da coluna ID para garantir que as linhas
                 sejam comparadas corretamente (ex: 'id', 'tempo', 'nó').
    """

    # 1. Carregar os dados
    try:
        df_power = pd.read_csv(arquivo_x)
        df_ana = pd.read_csv(arquivo_y, sep=";")
    except FileNotFoundError as e:
        print(f"Erro ao abrir arquivo: {e}")
        return

    df_ana = converter_para_float(df_ana[col_y])
    df_power = converter_para_float(df_power[col_x])

    # 3. Cálculo do Erro Percentual
    soma = df_power - df_ana

    erro = (soma / df_power) * 100
    erro_format = abs(erro)
    df = pd.DataFrame({"Erro (%)": erro_format})

    # Opcional: Salvar resultado em novo CSV
    df.to_csv(f"erros/resultado_comparacao{barras}.csv", index=False)
    print(f"\nArquivo 'resultado_comparacao{barras}.csv' salvo com sucesso.")


# --- CONFIGURAÇÃO ---
# Altere os nomes abaixo para os seus arquivos e colunas reais
arquivo_programa_x = "resultados/ieee57_pandapower.csv"
arquivo_programa_y = "resultados/ieee57_anarede.csv"
coluna_referencia = "vm_pu"  # Exemplo: nome da coluna no arquivo X
coluna_comparacao = "Tensao (p.u.)"  # Exemplo: nome da coluna no arquivo Y
barras = 57

# Executar
if __name__ == "__main__":
    # Chama a função
    calcular_erro_percentual(
        arquivo_programa_x,
        arquivo_programa_y,
        coluna_referencia,
        coluna_comparacao,
        barras,
    )
