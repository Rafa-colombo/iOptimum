# 🛠️ Heurística de Programação Semanal (PCM)

Este projeto implementa um sistema automatizado para alocação e programação semanal de Ordens de Serviço (OS) de Manutenção (PCM). Utilizando uma **heurística gulosa (greedy)**, o algoritmo processa um backlog de OS's e suas respectivas tarefas, distribuindo-as em uma janela de 5 dias úteis.

O objetivo principal é **maximizar a quantidade de OS's executadas**, priorizando as de maior criticidade e respeitando restrições rigorosas de tempo, capacidade de mão de obra e dependências técnicas.

---

## 📋 Regras de Negócio Implementadas

O núcleo da heurística avalia cada Ordem de Serviço contra 4 restrições fundamentais:

1. **Prioridade de Criticidade:** A alocação é tentada na ordem de importância: `Z` (Máxima) > `A` > `B` > `C` (Mínima).
2. **Predecessoras (Dependências):** Uma OS só é agendada se sua predecessora foi concluída. O sistema rastreia o dia e a hora exata do término da predecessora para iniciar a dependente.
3. **Condição de Parada de Planta:** OS's que exigem a fábrica parada (`parada == 'sim'`) só são alocadas em dias específicos informados no input.
4. **Limite Cronológico e Homem-Hora (HH):**
   * As tarefas são executadas em **série**. O dia possui um limite cronológico estrito de 8 horas.
   * O consumo de HH respeita o limite diário por habilidade (ex: Mecânica, Elétrica).
   * Se uma OS ultrapassa o tempo limite do dia, ela "transborda" sequencialmente para o dia útil seguinte.
   * **Rollback:** Se uma OS inicia, mas não consegue ser finalizada dentro dos 5 dias úteis da semana, sua alocação é desfeita para liberar recursos para OS's menores.

---

## 🏗️ Arquitetura de Dados

O sistema utiliza `dataclasses` do Python para estruturar os dados de forma tipada e eficiente:

* **`Tarefa`**: Menor unidade de trabalho (Habilidade, Duração, Quantidade de pessoas).
* **`OrdemServico`**: Agrupador de tarefas em série, contendo as regras de negócio (Prioridade, Parada, Predecessoras).
* **`PCMData`**: Struct de entrada que consolida o backlog de OS's, a capacidade diária de HH e os dias de parada.
* **`Solucao`**: Struct de saída que armazena a matriz de dias alocados, métricas de eficiência e logs adicionais.

---

## 🚀 Instalação e Execução

### Pré-requisitos

* Python 3.8+
* Biblioteca `pandas` (para leitura da base de dados)
* Biblioteca `openpyxl` (engine para ler arquivos `.xlsx`)

```bash
# Instalação das dependências
pip install pandas openpyxl