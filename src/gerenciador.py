import copy
from dataclasses import dataclass, field
from typing import Dict, List, Union, Any

# Structs fornecidas
@dataclass
class Tarefa:
    tarefa_num: str = ""
    habilidade: str = ""
    duracao_horas: float = 0.0
    quantidade: int = 1

@dataclass
class OrdemServico:
    id_os: Union[str, int] = ""
    prioridade: str = ""
    parada: str = ""
    predecessoras: List[str] = field(default_factory=list)
    tarefas: List[Tarefa] = field(default_factory=list)

@dataclass
class PCMData:
    ordens_servico: Dict[Union[str, int], OrdemServico] = field(default_factory=dict)
    capacidade_diaria_habilidade: Dict[int, Dict[str, float]] = field(default_factory=dict)
    dias_parada: List[int] = field(default_factory=list)

@dataclass
class Solucao:
    solution: Dict[Union[str, int], str] = field(default_factory=dict)
    metrics: Dict[str, Union[str, Dict[str, str]]] = field(default_factory=dict)
    extras: Dict[str, Any] = field(default_factory=dict)

# Classe Gerenciador
class GerenciadorCronograma:
    def __init__(self, dados_pcm: PCMData):
        self.dados_pcm = dados_pcm
        self.solucao_final = Solucao()
        
        # deepcopy das capacidades para ir deduzindo conforme alocado
        self.capacidade_restante = copy.deepcopy(dados_pcm.capacidade_diaria_habilidade)
        
        # Dicionário de controle: {id_os: (dia_fim, hora_fim_no_dia)}
        self.fim_os = {}

    def ordenar_os_por_prioridade(self):
        # Mapeamento para garantir a ordem correta de Z para C
        peso_prioridade = {'Z': 4, 'A': 3, 'B': 2, 'C': 1}
        return sorted(
            self.dados_pcm.ordens_servico.values(), 
            key=lambda os: peso_prioridade.get(os.prioridade.upper(), 0), 
            reverse=True
        )

    def gerenciador(self):
        """Implementa a lógica (greedy) de alocação."""
        for os in self.ordenar_os_por_prioridade():
            
            # Verifica se todas as predecessoras foram agendadas 
            predecessoras_ok = True
            dia_inicio = 1
            hora_inicio = 0.0
            
            for pred in os.predecessoras:
                if pred not in self.fim_os:
                    predecessoras_ok = False
                    break
                
                pred_dia, pred_hora = self.fim_os[pred]
                # A nova OS só pode começar após o término da predecessora
                if pred_dia > dia_inicio:
                    dia_inicio = pred_dia
                    hora_inicio = pred_hora
                elif pred_dia == dia_inicio and pred_hora > hora_inicio:
                    hora_inicio = pred_hora
                    
            if not predecessoras_ok:
                continue # Pula esta OS, a dependência falhou

            # Tenta agendar a OS
            self._tentar_alocar_os(os, dia_inicio, hora_inicio)

        return self.solucao_final

    def _tentar_alocar_os(self, os: OrdemServico, start_dia: int, start_hora: float):
        """Tenta encaixar todas as tarefas da OS. Se não couber na semana, faz rollback."""
        snapshot_capacidade = copy.deepcopy(self.capacidade_restante)
        
        dia_atual = start_dia
        hora_atual = start_hora
        dias_utilizados = set()
        sucesso_agendamento = True
        
        for tarefa in os.tarefas:
            duracao_restante = tarefa.duracao_horas
            
            while duracao_restante > 0:
                if dia_atual > 5: 
                    sucesso_agendamento = False
                    break
                
                # Restrição: Dia de Parada
                if os.parada.lower() == 'sim' and dia_atual not in self.dados_pcm.dias_parada:
                    dia_atual += 1
                    hora_atual = 0.0
                    continue
                
                # Restrição: 8 horas cronológicas por dia 
                tempo_cronologico_hoje = 8.0 - hora_atual
                if tempo_cronologico_hoje <= 0:
                    dia_atual += 1
                    hora_atual = 0.0
                    continue
                    
                # Inicializa o dia na capacidade caso não exista
                if dia_atual not in self.capacidade_restante:
                    self.capacidade_restante[dia_atual] = {}
                    
                cap_hab_hoje = self.capacidade_restante[dia_atual].get(tarefa.habilidade, 0.0)
                
                # Capacidade gasta = tempo * quantidade de pessoas. 
                if tarefa.quantidade > 0:
                    max_tempo_habilidade = cap_hab_hoje / tarefa.quantidade
                else:
                    max_tempo_habilidade = float('inf')
                
                # O que falta da tarefa, o tempo cronológico restante do dia, e a disponibilidade de skill
                tempo_a_alocar = min(duracao_restante, tempo_cronologico_hoje, max_tempo_habilidade)
                
                if tempo_a_alocar <= 0:
                    # Acabou o recurso (habilidade) para esse dia
                    dia_atual += 1
                    hora_atual = 0.0
                    continue
                
                # Aloca o tempo
                duracao_restante -= tempo_a_alocar
                hora_atual += tempo_a_alocar
                self.capacidade_restante[dia_atual][tarefa.habilidade] -= (tempo_a_alocar * tarefa.quantidade)
                dias_utilizados.add(dia_atual)

            if not sucesso_agendamento:
                break
                
        if sucesso_agendamento:
            # Salva exatamente onde a OS terminou para amarrar as predecessoras depois
            self.fim_os[os.id_os] = (dia_atual, hora_atual)
            dias_str = ", ".join(map(str, sorted(dias_utilizados)))
            self.solucao_final.solution[os.id_os] = dias_str
        else:
            # Rollback: A OS precisou estourar os 5 dias. Revertemos a capacidade gasta.
            self.capacidade_restante = snapshot_capacidade