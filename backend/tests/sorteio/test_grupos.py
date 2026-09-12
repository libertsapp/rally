from app.sorteio.modelos import JogadorSorteio
from app.sorteio.grupos import montar_grupos


def jogador(id, estrelas=3, sexo="M"):
    return JogadorSorteio(id=id, nome=f"J{id}", estrelas=estrelas, sexo=sexo)


def test_montar_grupos_cria_grupos_do_tamanho_de_um_time():
    jogadores = [jogador(str(i), estrelas=(i % 5) + 1) for i in range(12)]
    grupos = montar_grupos(jogadores, num_times=4)

    assert all(len(g) == 4 for g in grupos)
    # todo mundo aparece em algum grupo, sem duplicar ninguém
    todos_ids = [p.id for g in grupos for p in g]
    assert sorted(todos_ids) == sorted(p.id for p in jogadores)


def test_montar_grupos_mulheres_ficam_nos_ultimos_grupos():
    homens = [jogador(str(i), estrelas=5, sexo="M") for i in range(8)]
    mulheres = [jogador(f"f{i}", estrelas=5, sexo="F") for i in range(4)]
    grupos = montar_grupos(homens + mulheres, num_times=4)

    # 8 homens = 2 grupos completos; último grupo (índice 2) deve ser só mulheres
    assert all(p.sexo == "M" for p in grupos[0])
    assert all(p.sexo == "M" for p in grupos[1])
    assert all(p.sexo == "F" for p in grupos[2])


def test_montar_grupos_completa_grupo_de_mulheres_com_homens_de_menor_nota():
    # 3 mulheres, tamanho de grupo = 4 (num_times) -> falta 1 vaga, completada
    # pelo homem de MENOR nota entre os que sobraram
    homens = [jogador("forte", estrelas=5), jogador("fraco", estrelas=1)]
    mulheres = [jogador(f"f{i}", estrelas=5, sexo="F") for i in range(3)]
    grupos = montar_grupos(homens + mulheres, num_times=4)

    ultimo_grupo = grupos[-1]
    assert len(ultimo_grupo) == 4
    ids_ultimo_grupo = {p.id for p in ultimo_grupo}
    assert "fraco" in ids_ultimo_grupo
    assert "forte" not in ids_ultimo_grupo
