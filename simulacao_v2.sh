#!/bin/bash

# Diretório base onde as simulações estão localizadas
BASE_DIR="simulation_material_equivalent"

# Número total de primários desejado (1e10)
TOTAL_PRIMARIES=12000000

# Número de primários por execução (limite do GATE, 1e9)
PRIMARIES_PER_RUN=4000000

# Calcular o número de execuções necessárias
NUM_RUNS=$((TOTAL_PRIMARIES / PRIMARIES_PER_RUN))

# Verifica se o diretório base existe
if [ ! -d "$BASE_DIR" ]; then
    echo "Erro: O diretório base de simulações '$BASE_DIR' não foi encontrado."
    exit 1
fi

# Navega para o diretório base
cd "$BASE_DIR"

# Loop através de cada diretório de simulação (e.g., Simulation_PMMA, Simulation_PVC)
for SIM_DIR in Simulation_*/; do
    if [ -d "$SIM_DIR" ]; then
        echo "Entrando no diretório de simulação: $SIM_DIR"
        cd "$SIM_DIR"

        # Loop através de cada diretório de medida (e.g., Measure_1, Measure_2)
        for MEASURE_DIR in Measure_*/; do
            if [ -d "$MEASURE_DIR" ]; then
                echo "  Entrando no diretório de medida: $MEASURE_DIR"
                cd "$MEASURE_DIR"

                # Verifica se o arquivo main.mac existe
                if [ -f "main.mac" ]; then
                    echo "    Processando main.mac em $(pwd)"

                    # Cria um backup do main.mac original
                    cp main.mac main.mac.bak

                    # Loop para executar a simulação múltiplas vezes
                    for ((i=1; i<=NUM_RUNS; i++)); do
                        echo "      Execução $i de $NUM_RUNS para $(pwd)"

                        # Gerar uma nova semente aleatória para cada execução
                        # Usar a data/hora atual + contador para garantir unicidade
                        RANDOM_SEED=$(date +%s%N | cut -b1-9)

                        # Modificar main.mac para esta execução
                        # 1. Definir o número de primários por execução
                        # 2. Definir a semente aleatória
                        # 3. Modificar os nomes dos arquivos de saída para evitar sobrescrita
                        sed -i "s|^/gate/application/setTotalNumberOfPrimaries .*|/gate/application/setTotalNumberOfPrimaries ${PRIMARIES_PER_RUN}|g" main.mac
                        sed -i "s|^/gate/random/setEngineSeed .*|/gate/random/setEngineSeed ${RANDOM_SEED}|g" main.mac
                        sed -i "s|output/fluence_image.mhd|output/fluence_image_run${i}.mhd|g" main.mac
                        sed -i "s|output/fluence_image-scatter.mhd|output/fluence_image-scatter_run${i}.mhd|g" main.mac
                        sed -i "s|output/fluence_image.raw|output/fluence_image_run${i}.raw|g" main.mac
                        sed -i "s|output/fluence_image-scatter.raw|output/fluence_image-scatter_run${i}.raw|g" main.mac
                        sed -i "s|output/statsMC.txt|output/statsMC_run${i}.txt|g" main.mac

                        # Executar Gate
                        # Substitua 'Gate' pelo caminho completo do executável Gate se não estiver no PATH
                        # Gate main.mac  
                        Gate main.mac &> terminal.txt &

                        if [ $? -eq 0 ]; then
                            echo "        Simulação enviada com sucesso (Execução $i)."
                        else
                            echo "        Erro no envio da simulação (Execução $i)."
                        fi

			                  sleep 2
                        # Restaurar main.mac para o estado original antes da próxima modificação
                        
                        cp main.mac.bak main.mac
                    done

                    # Remover o backup após todas as execuções
                    rm main.mac.bak

                else
                    echo "    Aviso: main.mac não encontrado em $(pwd)"
                fi

                # Retorna ao diretório da simulação (e.g., Simulation_PMMA)
                cd ..
            fi
        done

        # Retorna ao diretório base
        cd ..
    fi
done

echo "Todas as simulações foram processadas com 1e10 primários (divididos em ${NUM_RUNS} execuções de ${PRIMARIES_PER_RUN})."
