"""Test della lettura e della disattivazione delle righe di /etc/fstab.

È il file più delicato del sistema: una riga sbagliata può impedire l'avvio
della macchina. Questi test verificano soprattutto che l'agent tocchi **solo**
la riga giusta, e che non cancelli mai nulla.
"""

from pathlib import Path

import pytest
from anf_agent import fstab
from anf_agent.protocol import ErroreAgent

_FSTAB = """\
# /etc/fstab: static file system information.
UUID=1234-5678  /               ext4    errors=remount-ro       0 1
UUID=abcd-ef01  /boot/efi       vfat    umask=0077              0 1

192.168.1.56:/volume2/Zipped  /srv/nas/zipped  nfs  ro,vers=3,noatime  0 0
192.168.1.56:/volume1/Foto    /srv/nas/foto    nfs4 rw,vers=4.1        0 0
# 192.168.1.56:/volume1/Vecchio /srv/nas/vecchio nfs ro 0 0
tmpfs           /tmp            tmpfs   defaults                0 0
"""


@pytest.fixture
def file_fstab(tmp_path: Path) -> Path:
    percorso = tmp_path / "fstab"
    percorso.write_text(_FSTAB, encoding="utf-8")
    return percorso


# --- lettura ---------------------------------------------------------------


def test_trova_solo_i_montaggi_nfs(file_fstab: Path) -> None:
    trovati = fstab.elenca(file_fstab)
    assert [m["mountpoint"] for m in trovati] == ["/srv/nas/zipped", "/srv/nas/foto"]


def test_separa_server_ed_esportazione(file_fstab: Path) -> None:
    primo = fstab.elenca(file_fstab)[0]
    assert primo["server"] == "192.168.1.56"
    assert primo["export"] == "/volume2/Zipped"
    assert primo["opzioni"] == "ro,vers=3,noatime"
    assert primo["tipo"] == "nfs"


def test_le_righe_commentate_non_compaiono(file_fstab: Path) -> None:
    """Sono già spente: proporle come da importare farebbe credere che siano in uso."""
    assert all("vecchio" not in m["mountpoint"] for m in fstab.elenca(file_fstab))


def test_un_fstab_assente_non_e_un_errore(tmp_path: Path) -> None:
    assert fstab.elenca(tmp_path / "non-esiste") == []


# --- disattivazione --------------------------------------------------------


def test_commenta_solo_la_riga_indicata(file_fstab: Path) -> None:
    esito = fstab.disattiva("/srv/nas/zipped", file_fstab)
    assert esito["righe"] == "1"

    contenuto = file_fstab.read_text(encoding="utf-8")
    assert "#192.168.1.56:/volume2/Zipped" in contenuto
    # L'altra riga NFS resta attiva, e così tutto il resto del file.
    assert "\n192.168.1.56:/volume1/Foto" in contenuto
    assert "UUID=1234-5678" in contenuto
    assert "tmpfs" in contenuto


def test_la_riga_non_viene_cancellata_ma_spiegata(file_fstab: Path) -> None:
    """Chi si trova davanti un fstab modificato deve capire cos'è successo."""
    fstab.disattiva("/srv/nas/foto", file_fstab)
    contenuto = file_fstab.read_text(encoding="utf-8")

    assert fstab.MARCATORE in contenuto
    assert "/volume1/Foto" in contenuto


def test_viene_lasciata_una_copia_di_sicurezza(file_fstab: Path, tmp_path: Path) -> None:
    esito = fstab.disattiva("/srv/nas/foto", file_fstab)

    copia = Path(esito["copia"])
    assert copia.exists()
    assert copia.read_text(encoding="utf-8") == _FSTAB


def test_un_mountpoint_inesistente_non_tocca_il_file(file_fstab: Path) -> None:
    prima = file_fstab.read_text(encoding="utf-8")

    with pytest.raises(ErroreAgent):
        fstab.disattiva("/srv/nas/inventato", file_fstab)

    assert file_fstab.read_text(encoding="utf-8") == prima


def test_una_riga_gia_commentata_non_si_ricommenta(file_fstab: Path) -> None:
    with pytest.raises(ErroreAgent):
        fstab.disattiva("/srv/nas/vecchio", file_fstab)
