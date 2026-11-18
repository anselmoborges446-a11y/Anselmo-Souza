import os
import numpy as np
import glob

def load_raw_image(raw_path, shape=(720, 720), dtype=np.float32):
    try:
        data = np.fromfile(raw_path, dtype=dtype)
        if data.size < shape[0] * shape[1]:
            return None
        return data[:shape[0] * shape[1]].reshape(shape)
    except Exception:
        return None

def process_simulation_folder(base_path, radius=200):
    results = {}
    height, width = 720, 720
    center_y, center_x = height // 2, width // 2
    y, x = np.ogrid[:height, :width]
    dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    mask = dist_from_center <= radius
    
    # Procurar por Measure_1 até Measure_5
    for i in range(1, 6):
        measure_dir = os.path.join(base_path, f"Measure_{i}", "output")
        if not os.path.exists(measure_dir):
            continue
            
        raw_files = glob.glob(os.path.join(measure_dir, "fluence_image_run*.raw"))
        raw_files = [f for f in raw_files if "-scatter" not in f]
        
        if not raw_files:
            continue
            
        all_pixels = []
        for raw_file in raw_files:
            img = load_raw_image(raw_file)
            if img is not None:
                all_pixels.extend(img[mask].tolist())
            
        if all_pixels:
            pixels_array = np.array(all_pixels)
            mean_val = np.mean(pixels_array)
            std_val = np.std(pixels_array)
            rel_error = std_val / mean_val if mean_val != 0 else 0
            results[f"Measure_{i}"] = (mean_val, std_val, rel_error)
            
    return results

def main():
    # Caminho atualizado após extração
    root_dir = "/home/ubuntu/simulacao_data/sim_mat_equ"
    parts = ["Parte1", "Parte2", "Parte3", "Parte4", "Parte5"]
    all_results = []
    
    # Processar a simulação do Vácuo na Parte3 (agora adicionada apenas como linha normal, já que I/I0 foi descartado)
    vacuum_path = os.path.join(root_dir, "Parte3", "Simulation_Vacuum")
    if os.path.exists(vacuum_path):
        i0_res = process_simulation_folder(vacuum_path, radius=200)
        for m, stats in sorted(i0_res.items()):
            all_results.append(("Simulation_Vacuum", m, *stats))
            
    for part in parts:
        part_path = os.path.join(root_dir, part)
        if not os.path.exists(part_path):
            continue
            
        sims = sorted([d for d in os.listdir(part_path) if os.path.isdir(os.path.join(part_path, d)) and d != "Simulation_Vacuum"])
        for sim in sims:
            res = process_simulation_folder(os.path.join(part_path, sim), radius=200)
            for m, stats in sorted(res.items()):
                all_results.append((f"{part}/{sim}", m, *stats))
                
    # Gerar saída em Markdown apenas com os dados solicitados
    output_file = "/home/ubuntu/tabela_r200.md"
    with open(output_file, "w") as f:
        f.write("# Tabela Consolidada de Resultados (Raio = 200 pixels)\n\n")
        f.write("| Simulação | Medida | Média (I) | Desvio Padrão | Erro Relativo |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for sim, m, mean, std, rel in all_results:
            f.write(f"| {sim} | {m} | {mean:.6e} | {std:.6e} | {rel:.6e} |\n")
    
    print(f"Processamento concluído. Resultados salvos em {output_file}")

if __name__ == "__main__":
    main()
