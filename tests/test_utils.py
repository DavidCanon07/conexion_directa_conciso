import pytest

from utils import manejar_errores


def test_manejar_errores_captura_filenotfound_y_devuelve_none(capsys):
    @manejar_errores
    def falla():
        raise FileNotFoundError("archivo.txt")

    resultado = falla()

    assert resultado is None
    assert "No se encontro el archivo" in capsys.readouterr().out or \
           "No se encontró el archivo" in capsys.readouterr().out


def test_manejar_errores_deja_pasar_el_valor_de_retorno_normal():
    @manejar_errores
    def ok():
        return 42

    assert ok() == 42


def test_manejar_errores_captura_excepcion_generica(capsys):
    @manejar_errores
    def falla():
        raise ValueError("dato invalido")

    resultado = falla()

    assert resultado is None
