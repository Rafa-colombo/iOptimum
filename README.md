# Heurística de Programação Semanal (PCM)

Este projeto implementa um sistema automatizado para alocação e programação semanal de Ordens de Serviço (OS) de Manutenção (PCM). Utilizando uma **heurística greedy (gulosa)**, o algoritmo processa um backlog de OS's e suas respectivas tarefas, distribuindo-as em uma janela de 5 dias úteis.

O objetivo principal é **maximizar a quantidade de OS's executadas**, priorizando as de maior criticidade e respeitando restrições rigorosas de tempo, capacidade de mão de obra e dependências técnicas.

---

## Estratégias de Resolução

A solução foi modelada sob uma abordagem greedy (*Greedy Algorithm*), onde as melhores escolhas locais (alocar as OS's mais críticas primeiro) são feitas na esperança de encontrar o melhor resultado global. As estratégias adotadas para contornar as restrições do problema foram:

1. **Ordenação por Criticidade:** Antes de qualquer alocação, a base de dados é ordenada pelo peso da prioridade: `Z` (Máxima) > `A` > `B` > `C` (Mínima).
2. **Gestão de Predecessoras (Grafo de Dependências):** Uma OS dependente só é processada após a validação de que sua predecessora foi concluída com sucesso. A heurística guarda o "dia" e a "hora exata" de término da OS pai, forçando a OS filha a iniciar cronologicamente após este marco.
3. **Controle de Tempo Duplo (Cronológico vs. Mão de Obra):** 
   * As tarefas ocorrem em **série**. Existe um teto cronológico rígido de 8 horas diárias.
   * Simultaneamente, há o teto de Homem-Hora (HH) disponível por habilidade (ex: Mecânica, Elétrica).
   * **Estratégia de Transbordo:** O avanço de uma tarefa é definido pelo menor valor entre o tempo necessário da tarefa, o tempo cronológico restante no dia, e a disponibilidade de skill. O que não cabe no dia, avança automaticamente para o dia seguinte.
4. **Mecanismo de Rollback:** Se uma OS inicia sua execução, mas suas tarefas ultrapassam o limite dos 5 dias úteis, o sistema aborta a alocação daquela OS e **desfaz (rollback)** o consumo de mão de obra, liberando espaço para que OS's menores possam ser agendadas.
5. **Paradas de Planta:** Filtro rígido onde OS's marcadas com `parada == 'sim'` pulam os dias úteis comuns até encontrarem um dia designado como dia de parada na matriz de entrada.

---

## Documentação do Código e Arquitetura do Sistema

O sistema foi arquitetado de forma modular, separando a ingestão de dados da lógica de negócio. Ele é implementado majoritariamente por dois scripts principais:

### 1. `gerenciador.py` (Core / Business Logic)
Agrega a estrutura de classes de dados e o motor da heurística.
* **Dataclasses (`Tarefa`, `OrdemServico`, `PCMData`, `Solucao`):** Estruturas que modelam os dados de forma tipada e eficiente em memória.
* **`GerenciadorCronograma` (ou `GerenciadorOperacoes`):** Classe responsável por rodar o algoritmo de alocação. Recebe os dados brutos, aplica as restrições (tempo, paradas, dependências) através do método interno `_tentar_alocar_os`, e gerencia o consumo do pool de habilidades.

### 2. `main.py` (Entrypoint / Data Ingestion)
Responsável por orquestrar a leitura e a saída de dados, sem carregar regras de negócio.
* **Leitura de Dados:** Utiliza `pandas` para extrair informações das abas do Excel e popular as `dataclasses`.
* **`create_solution`:** Função orquestradora que dita o fluxo de execução (Lê Excel -> Instancia Gerenciador -> Executa Heurística -> Prepara Saída).
* **Formatação de Saída:** Converte os objetos processados no formato de resposta JSON exigido.

---

## 📊 Apresentação dos Resultados

O programa gera um output em formato `JSON` estruturado em três eixos principais: **Solução** (em quais dias as OS's ocorreram), **Métricas** (KPIs de eficiência do algoritmo) e **Extras** (dados de auditoria e sobras de HH). 

Este formato atende perfeitamente à integração com dashboards e APIs de acompanhamento:

```json
{
    "solution": {
        "OS_10": "1",
        "OS_52": "1, 2",
        "OS_83": "3, 4, 5"
    },
    "metrics": {
        "n_os": "10", 
        "n_Z": "2", 
        "n_A": "3", 
        "n_B": "3", 
        "n_C": "2", 
        "utilization": {
            "mecanico": "85%", 
            "eletrico": "63%",
            "soldador": "10%"
        }
    },
    "extras": {
        "observations": "Heurística de alocação sequencial com limites diários concluída.",
        "plots": "Visualizações não geradas na rotina principal.",
        "any_additional_information": {
            "capacidade_restante_por_dia": {
                "1": {
                    "Mecânico": 1.5,
                    "Elétrico": 0.0
                }
            }
        }
    }
}

 ```
Os resultados da execução foram salvos no arquivo `output.json`
## Instalação e Execução
Atreração manual de caminho para arquivo excel. 
Mudar linha 145 no script main.py para alteração.
### Pré-requisitos

* Python 3.8+
* Biblioteca `pandas` (para leitura da base de dados)
* Biblioteca `openpyxl` (engine para ler arquivos `.xlsx`)

```bash
# Instalação das dependências
pip install pandas openpyxl
python .\src\main.py
