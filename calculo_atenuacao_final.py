import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt

"""
Script de Cálculo de Coeficientes de Atenuação Ponderados
Autor: Assistente de Programação Científica (Manus)
Data: 2026-06-01
"""

def carregar_dados_materiais():
    # Composições baseadas em NIST/ICRU-44
    materiais = {
        "PMMA": {"rho": 1.195, "comp": {"H": 0.0805, "C": 0.5999, "O": 0.3196}},
        "PE": {"rho": 0.96, "comp": {"H": 0.1437, "C": 0.8563}},
        "PET": {"rho": 1.4, "comp": {"H": 0.0420, "C": 0.6250, "O": 0.3330}},
        "ABS": {"rho": 1.03, "comp": {"H": 0.0811, "C": 0.8527, "N": 0.0662}},
        "PS": {"rho": 1.06, "comp": {"H": 0.0774, "C": 0.9226}},
        "Parafina": {"rho": 0.93, "comp": {"H": 0.1486, "C": 0.8514}},
        "PLA": {"rho": 1.24, "comp": {"H": 0.0559, "C": 0.5000, "O": 0.4441}},
        "PU_Tarugo": {"rho": 1.12, "comp": {"H": 0.071, "C": 0.612, "N": 0.071, "O": 0.246}},
        "PU_Espuma": {"rho": 0.026, "comp": {"H": 0.071, "C": 0.612, "N": 0.071, "O": 0.246}},
        "PA": {"rho": 1.13, "comp": {"H": 0.0980, "C": 0.6369, "N": 0.1238, "O": 0.1413}},
        "PVC": {"rho": 1.65, "comp": {"H": 0.0484, "C": 0.3844, "Cl": 0.5672}},
        "Musculo": {"rho": 1.05, "comp": {"H": 0.102, "C": 0.143, "N": 0.034, "O": 0.710, "Na": 0.001, "P": 0.002, "S": 0.003, "Cl": 0.001, "K": 0.004}},
        "Gordura": {"rho": 0.9, "comp": {"H": 0.114, "C": 0.598, "N": 0.007, "O": 0.278, "Na": 0.001, "S": 0.001, "Cl": 0.001}},
        "Pulmao": {"rho": 0.26, "comp": {"H": 0.103, "C": 0.105, "N": 0.031, "O": 0.749, "Na": 0.002, "P": 0.002, "S": 0.003, "Cl": 0.003, "K": 0.002}},
        "Figado": {"rho": 1.06, "comp": {"H": 0.102, "C": 0.139, "N": 0.030, "O": 0.716, "Na": 0.002, "P": 0.003, "S": 0.003, "Cl": 0.002, "K": 0.003}},
        "Osso": {"rho": 1.42, "comp": {"H": 0.047, "C": 0.144, "N": 0.042, "O": 0.446, "Mg": 0.002, "P": 0.105, "S": 0.003, "Ca": 0.209, "Zn": 0.002}},
        "Mama": {"rho": 1.02, "comp": {"H": 0.106, "C": 0.332, "N": 0.009, "O": 0.550, "Na": 0.001, "P": 0.001, "S": 0.001}}
    }
    return materiais

# Dados simplificados de mu/rho do NIST (cm2/g) para interpolação
nist_elements = {
    'H':  {'E': [1, 5, 10, 20, 30], 'mu': [7.27, 0.352, 0.322, 0.292, 0.272]},
    'C':  {'E': [1, 5, 10, 20, 30], 'mu': [2250, 24.1, 3.03, 0.444, 0.244]},
    'N':  {'E': [1, 5, 10, 20, 30], 'mu': [3540, 41.0, 5.34, 0.738, 0.334]},
    'O':  {'E': [1, 5, 10, 20, 30], 'mu': [5270, 65.8, 8.82, 1.20, 0.489]},
    'Cl': {'E': [1, 5, 10, 20, 30], 'mu': [1580, 963, 141, 19.8, 6.22]},
    'Na': {'E': [1, 5, 10, 20, 30], 'mu': [7590, 104, 14.3, 1.95, 0.722]},
    'Mg': {'E': [1, 5, 10, 20, 30], 'mu': [10500, 153, 21.6, 3.01, 1.05]},
    'P':  {'E': [1, 5, 10, 20, 30], 'mu': [18200, 302, 44.6, 6.42, 2.13]},
    'S':  {'E': [1, 5, 10, 20, 30], 'mu': [23000, 408, 61.5, 9.02, 3.02]},
    'K':  {'E': [1, 5, 10, 20, 30], 'mu': [35200, 722, 113, 17.3, 5.86]},
    'Ca': {'E': [1, 5, 10, 20, 30], 'mu': [42400, 926, 149, 23.2, 7.91]},
    'Zn': {'E': [1, 5, 10, 20, 30], 'mu': [12500, 219, 33.7, 53.0, 19.7]}
}

def interpolar_mu_rho(elemento, E_kev):
    data = nist_elements.get(elemento)
    if not data: return 0
    # Realiza interpolação log-log: transforma para log, interpola linearmente, e reverte para escala linear
    return np.exp(np.interp(np.log(E_kev), np.log(data["E"]), np.log(data["mu"])))

def processar_espectro(caminho_arquivo):
    df = pd.read_csv(caminho_arquivo, sep='\t')
    df.columns = ['energy_mev', 'fluence']
    df['energy_kev'] = df['energy_mev'] * 1000
    
    # Reduzir para intervalos de 1 keV
    df['bin'] = np.floor(df['energy_kev']).astype(int)
    grouped = df.groupby('bin').agg({'fluence': 'sum', 'energy_kev': 'mean'}).reset_index()
    
    # Normalizar pesos f(E)
    grouped['weight'] = grouped['fluence'] / grouped['fluence'].sum()
    return grouped

def calcular_atenuacao(materiais, espectro_reduzido):
    resultados = []
    for nome, info in materiais.items():
        rho = info['rho']
        comp = info['comp']
        u_ponderado = 0
        
        for _, row in espectro_reduzido.iterrows():
            E = row['energy_kev']
            w = row['weight']
            
            mu_rho_mix = sum(frac * interpolar_mu_rho(el, E) for el, frac in comp.items())
            u_E = mu_rho_mix * rho
            u_ponderado += u_E * w
            
        resultados.append({"Material": nome, "Densidade": rho, "u_ponderado": u_ponderado})
    return pd.DataFrame(resultados)

if __name__ == "__main__":
    # 1. Carregar Dados
    materiais = carregar_dados_materiais()
    espectro = processar_espectro('upload/energy_fluence_processed(1).txt')
    
    # 2. Calcular
    df_res = calcular_atenuacao(materiais, espectro)
    
    # 3. Exibir Resultados
    print("\n--- Resultados de Atenuação Ponderada ---")
    print(df_res.to_string(index=False))
    
    # 4. Gerar Gráfico
    plt.figure(figsize=(12, 6))
    plt.bar(df_res['Material'], df_res['u_ponderado'], color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('u ponderado (cm-1)')
    plt.title('Coeficientes de Atenuação Ponderados por Material')
    plt.tight_layout()
    plt.savefig('grafico_atenuacao.png')
    print("\nGráfico salvo como 'grafico_atenuacao.png'")
