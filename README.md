# 🇺🇸 English

**About the Project**
This project uses the Pandapower library to perform power flow simulations on electrical grids (such as the IEEE system) and provides tools for custom network creation and error analysis. It aims to facilitate the integration and comparison of results, possibly within the context of ANAREDE studies.

**Project Structure**
Below is a detailed explanation of each file and folder in this repository:

**Main Scripts**
simular_ieee2.py (Definitive): This is the main simulation script. It contains the definitive implementation for simulating the IEEE network using Pandapower. Use this file to run the project's standard power flow simulations.

power_grid_simulation.py (Custom Network): Script designed for creating custom networks. Use this file as a template if you need to build your own power grid topology instead of using the standard IEEE models.

erro.py (Error Analysis): Comparison tool. This script reads two columns from different files, compares the values, computes the absolute error, and outputs a .csv file with the results in the errors folder.

**Helper and Legacy Scripts**
pu_to_unit.py: Helper module containing parameter conversion functions (e.g., from p.u. to physical units). It is imported and used by the main scripts.

**Output Folders**
/resultados: Directory where the power flow simulation results are saved.

/erros: Directory where the erro.py script saves the .csv reports containing the comparisons and absolute error calculations.

**How to Use**
**1. Prerequisites**

Ensure you have Python installed along with the necessary libraries. It is recommended to use venv.
**-Using venv**

To create a virtual environment, run:

```bash
python -m venv venv

To activate the virtual environment, run:

```bash
venv\Scripts\activate
```

To install the dependencies, run:

```bash
pip install -r requirements.txt
```

**2. Running the IEEE Simulation (Definitive)**
To run the IEEE network simulation, execute the following command in your terminal:

```bash
python simular_ieee2.py
```
Results will be generated in the /resultados folder.

**3. Creating Your Own Network**
To create and simulate a custom network, edit the power_grid_simulation.py file and run:

```bash
python power_grid_simulation.py
```

**4. Calculating Errors**
To compare results and generate an error report, ensure the input files (that you wish to compare) are correctly configured inside the erro.py script.

Run the script:

```bash
python erro.py
```
The CSV file with the absolute error will be saved in the /erros folder.



# 🇧🇷 Português

**Sobre o Projeto**
Este projeto utiliza a biblioteca Pandapower para realizar simulações de fluxo de potência em redes elétricas (como o sistema IEEE) e oferece ferramentas para criação de redes personalizadas e análise de erros. O objetivo é facilitar a integração e comparação de resultados, possivelmente no contexto de estudos envolvendo o ANAREDE.

**Estrutura do Projeto**
Abaixo está a explicação detalhada de cada arquivo e pasta contida neste repositório:

**Scripts Principais**
simular_ieee2.py (Definitivo): Este é o script principal para simulação. Ele contém a implementação definitiva para simular a rede IEEE utilizando o Pandapower. Utilize este arquivo para rodar os fluxos de potência padrão do projeto.

power_grid_simulation.py (Criação de Rede): Script destinado à criação de redes personalizadas. Use este arquivo como base se você precisa montar sua própria topologia de rede elétrica ao invés de usar os modelos IEEE padrão.

erro.py (Análise de Erro): Ferramenta de comparação. Este script lê duas colunas de arquivos distintos, compara os valores e calcula o erro absoluto, gerando um arquivo .csv com os resultados dessa análise na pasta de erros.

**Scripts Auxiliares e Antigos**
pu_to_unit.py: Módulo auxiliar que contém funções de conversão de parâmetros (ex: de p.u. para unidades físicas). É importado e utilizado pelos scripts principais.

**Pastas de Saída**
/resultados: Diretório onde são salvos os resultados das simulações de fluxo de potência.

/erros: Diretório onde o script erro.py salva os relatórios .csv contendo as comparações e cálculos de erro absoluto.

**Como Usar**

**1. Pré-requisitos**
Certifique-se de ter o Python instalado e as bibliotecas necessárias. Recomenda-se o uso de venv. 

**Utilizando venv**

Para criar um ambiente virtual, execute o seguinte comando:

```bash
python -m venv venv
```

Para ativar o ambiente virtual, execute o seguinte comando:

```bash
venv\Scripts\activate
```

Para instalar as dependências, execute o seguinte comando:

```bash
pip install -r requirements.txt
```

**2. Executando a Simulação IEEE (Definitiva)**
Para rodar a simulação da rede IEEE, execute o seguinte comando no terminal:

```bash
python simular_ieee2.py
```
Os resultados serão gerados na pasta /resultados.

**3. Criando sua Própria Rede**
Para criar e simular uma rede personalizada, edite e execute:

```bash
python power_grid_simulation.py
```

**4. Calculando Erros**
Para comparar resultados e gerar um relatório de erros:

Verifique se os arquivos de entrada (que você deseja comparar) estão configurados corretamente dentro do script erro.py.

Execute o script:

```bash
python erro.py
```
O arquivo CSV com o erro absoluto será salvo na pasta /erros.
