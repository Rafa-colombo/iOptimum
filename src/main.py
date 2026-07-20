import json
from collections import Counter
from dataclasses import asdict

from gerenciador import GerenciadorCronograma, PCMData, OrdemServico, Tarefa, Solucao



def ler_excel_e_montar_dataclasses(excel_path: str) -> PCMData:
    """Ler Excel e montar o objeto PCMData com ordens, tarefas e capacidade."""
    import pandas as pd

    df_os = pd.read_excel(excel_path, sheet_name="OS")
    df_tarefas = pd.read_excel(excel_path, sheet_name="Tarefas")
    df_recursos = pd.read_excel(excel_path, sheet_name="Recursos")
    df_paradas = pd.read_excel(excel_path, sheet_name="Paradas")

    ordens_servico_dict = {}

    for _, row in df_os.iterrows():
        os_id = row["OS"]

        predecessoras = []
        if pd.notna(row.get("Predecessora")):
            predecessoras = [p.strip() for p in str(row["Predecessora"]).split(",") if p.strip()]

        ordens_servico_dict[os_id] = OrdemServico(
            id_os=os_id,
            prioridade=str(row.get("Prioridade", "")).strip(),
            parada=str(row.get("Condição", "")).strip(),
            predecessoras=predecessoras,
            tarefas=[],
        )

    for _, row in df_tarefas.iterrows():
        tarefa = Tarefa(
            tarefa_num=str(row.get("Tarefa", "")).strip(),
            habilidade=str(row.get("Habilidade", "")).strip(),
            duracao_horas=float(row.get("Duração", 0) or 0),
            quantidade=int(row.get("Quantidade", 1) or 1),
        )

        os_id = row["OS"]
        if os_id in ordens_servico_dict:
            ordens_servico_dict[os_id].tarefas.append(tarefa)

    recursos_diario_dict = {}
    for _, row in df_recursos.iterrows():
        dia = int(str(row["Dia"]).replace("Dia_", ""))
        habilidade = str(row["Habilidade"]).strip()
        horas = float(row["HH_Disponivel"])

        recursos_diario_dict.setdefault(dia, {})
        recursos_diario_dict[dia][habilidade] = horas

    dias_parada_list = df_paradas["Dia"].dropna().astype(int).tolist()

    return PCMData(
        ordens_servico=ordens_servico_dict,
        capacidade_diaria_habilidade=recursos_diario_dict,
        dias_parada=dias_parada_list,
    )


def montar_dicionario_saida(dados_pcm: PCMData) -> dict:
    """ Monta a saída como template exigido. """
    # Lógica
    gerenciador = GerenciadorCronograma(dados_pcm)
    solucao_final = gerenciador.gerenciador()

    # Calcular métricas de OS por prioridade
    n_os = len(solucao_final.solution)
    contagem_prioridade = {'Z': 0, 'A': 0, 'B': 0, 'C': 0}

    for os_id in solucao_final.solution.keys():
        prioridade_os = str(dados_pcm.ordens_servico[os_id].prioridade).strip().upper()
        if prioridade_os in contagem_prioridade:
            contagem_prioridade[prioridade_os] += 1

    # Calcular a utilização (%) de cada habilidade
    capacidade_total = {}
    capacidade_restante = {}

    # Somar capacidade total (da base original)
    for dia, habilidades in dados_pcm.capacidade_diaria_habilidade.items():
        for hab, horas in habilidades.items():
            capacidade_total[hab] = capacidade_total.get(hab, 0.0) + horas

    # Somar capacidade restante (do gerenciador após a execução)
    for dia, habilidades in gerenciador.capacidade_restante.items():
        for hab, horas in habilidades.items():
            capacidade_restante[hab] = capacidade_restante.get(hab, 0.0) + horas

    # Montar o dicionário de utilization no formato "XX%"
    utilization = {}
    for hab, total_horas in capacidade_total.items():
        if total_horas > 0:
            horas_sobrou = capacidade_restante.get(hab, 0.0)
            horas_usadas = total_horas - horas_sobrou
            percentual = (horas_usadas / total_horas) * 100
            utilization[hab.lower()] = f"{int(percentual)}%" 
        else:
            utilization[hab.lower()] = "0%"

    # Preencher a estrutura de métricas
    solucao_final.metrics = {
        "n_os": str(n_os),
        "n_Z": str(contagem_prioridade['Z']),
        "n_A": str(contagem_prioridade['A']),
        "n_B": str(contagem_prioridade['B']),
        "n_C": str(contagem_prioridade['C']),
        "utilization": utilization
    }

    # Preencher a estrutura de extras
    solucao_final.extras = {
        "observations": "Heurística de alocação sequencial com limites diários concluída.",
        "plots": "Visualizações não geradas na rotina principal.",
        "any_additional_information": {
            "capacidade_restante_por_dia": gerenciador.capacidade_restante
        }
    }

    return asdict(solucao_final)


def create_solution(excel_path: str) -> dict:
    """Executa o fluxo completo: lê o Excel, processa os dados e monta a saída final."""
    dados_iniciais = ler_excel_e_montar_dataclasses(excel_path)
    output_solution = montar_dicionario_saida(dados_iniciais)
    return output_solution


def salvar_struct_json(excel_path: str):
    """Salva o conteúdo das dataclasses em um JSON(debugg)."""
    resultado_dataclass = ler_excel_e_montar_dataclasses(excel_path)
    resultado_dict = asdict(resultado_dataclass)
    resultado_json = json.dumps(resultado_dict, indent=4, ensure_ascii=False)

    with open(r"D:\Python\iOptimum\data\resultado.json", "w", encoding="utf-8") as arquivo:
        arquivo.write(resultado_json)


if __name__ == "__main__":
    excel_path = r"D:\Python\iOptimum\data\backlog_desafio_500.xlsx"

    salvar_struct_json(excel_path)

    resultado = create_solution(excel_path)
    json_formatado = json.dumps(resultado, indent=4, ensure_ascii=False)
    print(json_formatado)

