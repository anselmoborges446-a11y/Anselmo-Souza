import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

"""
Script de Validação: Tecidos Alvo vs. Simuladores Poliméricos
Foco: Músculo, Gordura, Fígado, Osso e Mama.
"""

# 1. Definição dos Pares (Tecido Alvo vs Simulador)
# Dados de densidade e composição baseados em NIST/ICRU-44
materiais = {
    # Tecidos Biológicos
    "Músculo": {"rho": 1.05, "comp": {"H": 0.102, "C": 0.143, "N": 0.034, "O": 0.710, "Na": 0.001, "P": 0.002, "S": 0.003, "Cl": 0.001, "K": 0.004}},
    "Gordura": {"rho": 0.9, "comp": {"H": 0.114, "C": 0.598, "N": 0.007, "O": 0.278, "Na": 0.001, "S": 0.001, "Cl": 0.001}},
    "Fígado":  {"rho": 1.06, "comp": {"H": 0.102, "C": 0.139, "N": 0.030, "O": 0.716, "Na": 0.002, "P": 0.003, "S": 0.003, "Cl": 0.002, "K": 0.003}},
    "Osso":    {"rho": 1.42, "comp": {"H": 0.047, "C": 0.144, "N": 0.042, "O": 0.446, "Mg": 0.002, "P": 0.105, "S": 0.003, "Ca": 0.209, "Zn": 0.002}},
    "Mama":    {"rho": 1.02, "comp": {"H": 0.106, "C": 0.332, "N": 0.009, "O": 0.550, "Na": 0.001, "P": 0.001, "S": 0.001}},
    
    # Simuladores Poliméricos Correspondentes
    "PET (Sim. Músculo)": {"rho": 1.4, "comp": {"H": 0.0420, "C": 0.6250, "O": 0.3330}},
    "PE (Sim. Gordura)":  {"rho": 0.96, "comp": {"H": 0.1437, "C": 0.8563}},
    "PU Tarugo (Sim. Fígado)": {"rho": 1.12, "comp": {"H": 0.071, "C": 0.612, "N": 0.071, "O": 0.246}},
    "PVC (Sim. Osso)":    {"rho": 1.65, "comp": {"H": 0.0484, "C": 0.3844, "Cl": 0.5672}},
    "PLA (Sim. Mama)":    {"rho": 1.24, "comp": {"H": 0.0559, "C": 0.5000, "O": 0.4441}}
}

# Dados de mu/rho do NIST para interpolação log-log
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
    # Interpolação Log-Log para máxima precisão
    return np.exp(np.interp(np.log(E_kev), np.log(data['E']), np.log(data['mu'])))

def processar_espectro(caminho):
    df = pd.read_csv(caminho, sep='\t')
    df.columns = ['energy_mev', 'fluence']
    df['energy_kev'] = df['energy_mev'] * 1000
    df['bin'] = np.floor(df['energy_kev']).astype(int)
    grouped = df.groupby('bin').agg({'fluence': 'sum', 'energy_kev': 'mean'}).reset_index()
    grouped['weight'] = grouped['fluence'] / grouped['fluence'].sum()
    return grouped

if __name__ == "__main__":
    # Carregar espectro
    espectro = processar_espectro('upload/energy_fluence_processed(1).txt')
    
    resultados = []
    for nome, info in materiais.items():
        rho = info['rho']
        comp = info['comp']
        u_ponderado = 0
        
        for _, row in espectro.iterrows():
            E = row['energy_kev']
            w = row['weight']
            mu_rho_mix = sum(frac * interpolar_mu_rho(el, E) for el, frac in comp.items())
            u_ponderado += (mu_rho_mix * rho) * w
            
        resultados.append({"Material": nome, "u_ponderado": u_ponderado})
    
    df_res = pd.DataFrame(resultados)
    
    # Exibição organizada
    print("\n" + "="*50)
    print(" VALIDAÇÃO: TECIDOS ALVO VS. SIMULADORES")
    print("="*50)
    print(df_res.to_string(index=False))
    print("="*50)

    # Gráfico de Comparação Lado a Lado
    pares = [
        ("Músculo", "PET (Sim. Músculo)"),
        ("Gordura", "PE (Sim. Gordura)"),
        ("Fígado", "PU Tarugo (Sim. Fígado)"),
        ("Osso", "PVC (Sim. Osso)"),
        ("Mama", "PLA (Sim. Mama)")
    ]
    
    # Preparar dados para o gráfico
    nomes_tecido = [p[0] for p in pares]
    vals_tecido = [df_res[df_res['Material'] == p[0]]['u_ponderado'].values[0] for p in pares]
    vals_simul = [df_res[df_res['Material'] == p[1]]['u_ponderado'].values[0] for p in pares]

    x = np.arange(len(nomes_tecido))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 7))
    rects1 = ax.bar(x - width/2, vals_tecido, width, label='Tecido Alvo', color='#3498db')
    rects2 = ax.bar(x + width/2, vals_simul, width, label='Simulador', color='#e74c3c')

    ax.set_ylabel('u ponderado (cm-1)')
    ax.set_title('Comparação de Atenuação: Tecidos Biológicos vs. Simuladores Poliméricos')
    ax.set_xticks(x)
    ax.set_xticklabels(nomes_tecido)
    ax.legend()
    
    # Escala logarítmica no eixo Y para melhor visualização (devido ao Osso/PVC)
    ax.set_yscale('log')
    ax.set_ylim(0.1, 100)
    ax.grid(True, which="both", ls="-", alpha=0.2)

    plt.tight_layout()
    plt.savefig('validacao_simuladores.png')
    print("\nGráfico de validação salvo como 'validacao_simuladores.png'")
