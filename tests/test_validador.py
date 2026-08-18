from pathlib import Path

from validador import extraer_dia


def test_extraer_dia_patron_valido(tmp_path):
    ruta = tmp_path / "GOF.GRB.FM14.F260813.txt"
    ruta.write_text("x")

    assert extraer_dia(ruta) == "13"


def test_extraer_dia_fallback_pide_input(tmp_path, monkeypatch):
    ruta = tmp_path / "archivo_sin_patron.txt"
    ruta.write_text("x")
    monkeypatch.setattr("builtins.input", lambda _: "09")

    assert extraer_dia(ruta) == "09"
