"""Checkpoint atômico periódico dos runners Python — o requisito novo da DI-43.

**A decisão do autor (DI-43, ratificada na DI-44):** com o teto de 12 h e o rito
de *truncamento-com-dado*, "curva parcial é o dado" (DI-37.1) — mas isso só vale
se o dado EXISTIR quando o run morre de morte matada. Na rodada-42, um run que
levava 8 h e era interrompido (spot revogada, OOM, SIGKILL, teto do orquestrador)
não deixava **nenhum** parquet: as 4 camadas só nascem no `write_run_outputs`, no
fim. Este módulo grava as camadas PARCIAIS ao longo do caminho.

**Cadência (DI-43):** a cada **K=25 iterações OU 30 min**, o que vier primeiro.

**Três invariantes que este módulo NÃO pode violar:**

1. **Não muda o resultado.** O checkpoint só LÊ o buffer e o orçamento e serializa
   — zero RNG, zero decisão, zero mutação de estado. Um run completo sai
   bit-idêntico ao de antes (é o teste `test_checkpoint_nao_muda_o_resultado`).
2. **Escreve nos MESMOS caminhos das camadas finais**, atomicamente (tmp+rename,
   via `src.export`/`src.atomic_io`). O checkpoint N+1 sobrescreve o N; o
   `write_run_outputs` do fim sobrescreve o último. Nunca há artefato extra para
   o preflight anti-forasteiro tropeçar.
3. **Deixa o ⑤ COERENTE.** Camadas sem manifesto = célula "SEM-MANIFESTO" para o
   censo (o buraco do O-21). Cada checkpoint grava um ⑤ `failed` com
   `motivo_parada='checkpoint_em_andamento'` e o bloco `checkpoint`: se o run
   morrer, a célula fica honesta (`is_run_done`⇒False ⇒ re-run) e diagnosticável;
   se o run terminar, o manifesto real passa por cima.

**A ordem das 5 escritas é o contrato (achado do kill-test).** Cada arquivo é
atômico, mas o CONJUNTO não pode ser: um SIGKILL entre a ① e o ⑤ deixaria as duas
camadas em checkpoints diferentes. Por isso o **⑤ é gravado por ÚLTIMO** e a
regra fica declarada: em manifesto `checkpoint_em_andamento`, **`fe_final` é um
PISO** do que as camadas contêm (o run pode ter avançado 1 checkpoint além), nunca
uma promessa acima delas. A direção importa: um ⑤ *atrás* subdeclara dado que
existe; um ⑤ *à frente* prometeria dado que não existe — e é essa a mentira que a
campanha não pode ter. Medido no kill-test: ⑤ com `fe_final=11` e ① com 12 linhas.
"""

from __future__ import annotations

import time

from src import export as _export
from src import manifest as _manifest
from src import naming

#: [DI-43] Cadência do checkpoint: 25 iterações OU 30 min, o que vier primeiro.
K_ITER_DEFAULT: int = 25
INTERVALO_S_DEFAULT: float = 1800.0


class Checkpointer:
    """Grava as camadas parciais de um run em curso (DI-43).

    Uso nos runners (2 linhas):

        ckpt = Checkpointer(exp, alg, problema, semente, D=D, M=M,
                            regime='online', data_root=data_root, log=log)
        ...   # dentro do laço, DEPOIS de o buffer receber a iteração:
        ckpt.talvez_gravar(bud, buf, iteracao=it)

    `talvez_gravar` devolve `True` quando gravou. Falha de escrita NUNCA mata o
    run (mesma doutrina do dual-write, DI-42.3): o checkpoint é rede de
    segurança, não pode ser causa de morte — o erro vai para o ⑥ como guarda.
    """

    def __init__(self, exp: str, alg: str, problema: str, semente, *,
                 D: int, M: int, regime: str = "online",
                 q: int = 1, tier: str | None = None, dist: str | None = None,
                 data_root: str = naming.DEFAULT_DATA_ROOT,
                 log=None,
                 k_iter: int | None = None,
                 intervalo_s: float | None = None,
                 ativo: bool = True) -> None:
        self.exp, self.alg, self.problema, self.semente = exp, alg, problema, semente
        self.D, self.M, self.regime = int(D), int(M), regime
        self.q, self.tier, self.dist = int(q), tier, dist
        self.data_root, self.log = data_root, log
        # os defaults são lidos em RUNTIME (não na assinatura): é o que permite
        # ao teste/kill-test forçar cadência 1 sem tocar em cada runner.
        self.k_iter = int(K_ITER_DEFAULT if k_iter is None else k_iter)
        self.intervalo_s = float(INTERVALO_S_DEFAULT if intervalo_s is None
                                 else intervalo_s)
        self.ativo = bool(ativo)
        self.n_checkpoints = 0
        self.tempo_total_s = 0.0
        self._tempo_creditado_s = 0.0
        self._ultimo_t = time.time()
        self._ultima_iter = 0

    # -- decisão ------------------------------------------------------------
    def devido(self, iteracao: int, *, agora: float | None = None) -> bool:
        """A cadência DI-43 venceu? (iterações OU tempo — o que vier primeiro)"""
        if not self.ativo:
            return False
        agora = time.time() if agora is None else agora
        return (int(iteracao) - self._ultima_iter >= self.k_iter
                or (agora - self._ultimo_t) >= self.intervalo_s)

    def talvez_gravar(self, bud, buf, *, iteracao: int,
                      forcar: bool = False) -> bool:
        if not (forcar or self.devido(iteracao)):
            return False
        return self.gravar(bud, buf, iteracao=iteracao)

    # -- escrita ------------------------------------------------------------
    def gravar(self, bud, buf, *, iteracao: int) -> bool:
        """As 4 camadas + um ⑤ coerente, atomicamente. Nunca levanta."""
        t0 = time.time()
        args = (self.exp, self.alg, self.problema, self.semente)
        try:
            _export.write_real(*args, bud.records, data_root=self.data_root)
            _export.write_pop(*args, buf.pop_rows, data_root=self.data_root)
            _export.write_surrogate(*args, buf.surr_rows, D=self.D, M=self.M,
                                    regime=self.regime, data_root=self.data_root)
            _export.write_timing(*args, buf.timing_rows, data_root=self.data_root)
            self._manifesto_parcial(bud, iteracao=iteracao)
        except Exception as e:            # noqa: BLE001 — rede de segurança não mata run
            if self.log is not None:
                self.log.guard('checkpoint_falhou', iteracao=int(iteracao),
                               err=f'{type(e).__name__}: {e}')
            return False
        dt = time.time() - t0
        self.n_checkpoints += 1
        self.tempo_total_s += dt
        self._ultimo_t, self._ultima_iter = time.time(), int(iteracao)
        if self.log is not None:
            # o custo do instrumento é MEDIDO e fica no ⑥ (§17.6): a campanha
            # precisa saber quanto o checkpoint cobrou antes de mexer na cadência.
            self.log.event('checkpoint', iteracao=int(iteracao), fe=int(bud.fe),
                           n_linhas_terceira=len(buf.surr_rows),
                           n_checkpoints=self.n_checkpoints,
                           tempo_checkpoint_s=round(dt, 4))
        return True

    def _manifesto_parcial(self, bud, *, iteracao: int) -> None:
        """⑤ `failed`/`checkpoint_em_andamento` — camadas sem ⑤ são invisíveis
        para o censo (é o buraco do O-21, e o `is_run_done` tem de dizer NÃO).

        Gravado por ÚLTIMO de propósito: `fe_final` é PISO das camadas (ver o
        docstring do módulo), nunca promessa acima delas."""
        man = _manifest.new_manifest(
            self.exp, self.alg, self.problema, self.semente,
            status='failed', regime=self.regime, q=self.q,
            tier=self.tier, dist=self.dist,
            maxfe=int(bud.maxfe), fe_final=int(bud.fe),
            n_geracoes=int(iteracao), data_root=self.data_root, bucket=None)
        man['motivo_parada'] = 'checkpoint_em_andamento'
        man['checkpoint'] = {'iteracao': int(iteracao), 'fe': int(bud.fe),
                             'n_checkpoints': self.n_checkpoints + 1,
                             'ts': _manifest._utcnow_iso(),
                             'nota': ('fe/fe_final = PISO das camadas: o ⑤ é '
                                      'gravado por último, então um kill pode '
                                      'deixar as camadas 1 checkpoint à frente')}
        _manifest.write_manifest(man, self.data_root)

    # -- contabilidade de tempo (BL-11) -------------------------------------
    def consumir_tempo_s(self) -> float:
        """O I/O de checkpoint acumulado DESDE a última chamada; zera o ponteiro.

        [BL-11] `tempo_busca_s`/`tempo_geracao_s` medem o ALGORITMO; o
        checkpoint é instrumentação DESTA campanha (mesma doutrina da sonda,
        DI-13.10) e tem de sair da conta — mas não pode sumir, senão a R4 não
        explica o buraco entre Σ`tempo_geracao_s` e `tempo_total_s`. Esta é a
        primitiva que os 8 runners usam para publicá-lo em `tempo_checkpoint_s`
        (④) por geração: devolve **0.0** quando nada foi gravado no intervalo,
        que é o valor honesto (≠ NULL = "este config não faz checkpoint").
        """
        dt = self.tempo_total_s - self._tempo_creditado_s
        self._tempo_creditado_s = self.tempo_total_s
        return dt

    # -- relato -------------------------------------------------------------
    def resumo(self) -> dict:
        """Vai ao ⑤ final: quantos checkpoints e quanto custaram."""
        return {'n_checkpoints': self.n_checkpoints,
                'tempo_total_s': round(self.tempo_total_s, 4),
                'k_iter': self.k_iter, 'intervalo_s': self.intervalo_s}


__all__ = ['Checkpointer', 'K_ITER_DEFAULT', 'INTERVALO_S_DEFAULT']
