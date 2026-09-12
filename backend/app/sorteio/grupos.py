"""Porta de montarGrupos (modo manual: grupos por nível)."""

from __future__ import annotations

import random

from app.sorteio.draft import peso_de
from app.sorteio.modelos import JogadorSorteio


def montar_grupos(
    jogadores: list[JogadorSorteio], num_times: int
) -> list[list[JogadorSorteio]]:
    homens = [p for p in jogadores if p.sexo != "F"]
    random.shuffle(homens)
    homens.sort(key=peso_de, reverse=True)  # sort estável: empates ficam na ordem embaralhada

    mulheres = [p for p in jogadores if p.sexo == "F"]
    random.shuffle(mulheres)
    mulheres.sort(key=peso_de, reverse=True)

    # as mulheres sempre ficam no(s) último(s) grupo(s), e esse(s) grupo(s) sempre
    # tem exatamente o tamanho de um time (num_times) — se sobrar vaga depois de
    # colocar todas as mulheres, ela é preenchida pelos homens de MENOR nota
    homens_restantes = homens[:]
    pool_mulheres = mulheres[:]
    if pool_mulheres:
        qtd_grupos_mulheres = -(-len(pool_mulheres) // num_times)  # ceil
        vagas_faltando = (qtd_grupos_mulheres * num_times) - len(pool_mulheres)
        if vagas_faltando > 0:
            corte = max(0, len(homens_restantes) - vagas_faltando)
            homens_de_menor_nota = homens_restantes[corte:]
            del homens_restantes[corte:]
            pool_mulheres = pool_mulheres + homens_de_menor_nota

    def em_grupos(lista: list[JogadorSorteio]) -> list[list[JogadorSorteio]]:
        return [lista[i : i + num_times] for i in range(0, len(lista), num_times)]

    return em_grupos(homens_restantes) + em_grupos(pool_mulheres)
