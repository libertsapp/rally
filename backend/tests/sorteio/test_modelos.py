from app.sorteio.modelos import JogadorSorteio


def test_jogador_sorteio_aceita_campos_minimos_com_defaults():
    p = JogadorSorteio(id="1", nome="Ana")

    assert p.id == "1"
    assert p.nome == "Ana"
    assert p.estrelas == 0
    assert p.sexo == ""
    assert p.porte == ""
