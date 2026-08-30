"""Dati di scatto di una fotografia.

Sono le informazioni che la macchina scrive dentro il file: quando è stata
scattata, con che apparecchio, con che tempi. Il pannello le legge e basta —
non le modifica mai, perché riscrivere il file significherebbe alterare
l'originale di qualcun altro per mostrare una schermata.

Perché contano più di quanto sembri: la data di modifica di un file sul NAS è
quasi sempre la data in cui è stato **copiato**, non quella dello scatto.
Ordinare o raggruppare per quella significa mettere in fila le foto nell'ordine
in cui sono state travasate, che non è mai l'ordine che si ha in mente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

from PIL import ExifTags, Image, UnidentifiedImageError

#: Identificativi dei campi che ci interessano, per nome invece che per numero.
_CAMPI = {nome: numero for numero, nome in ExifTags.TAGS.items()}
_GPS = {nome: numero for numero, nome in ExifTags.GPSTAGS.items()}


@dataclass(frozen=True, slots=True)
class DatiScatto:
    """Quello che sappiamo di una foto. Ogni campo può mancare."""

    scattata: datetime | None = None
    fotocamera: str | None = None
    obiettivo: str | None = None
    tempo: str | None = None
    diaframma: str | None = None
    iso: int | None = None
    focale: str | None = None
    latitudine: float | None = None
    longitudine: float | None = None
    larghezza: int | None = None
    altezza: int | None = None

    @property
    def vuoto(self) -> bool:
        """Vero quando non c'è niente da mostrare oltre alle dimensioni."""
        return all(
            getattr(self, campo) is None
            for campo in ("scattata", "fotocamera", "tempo", "diaframma", "iso", "focale")
        )


def _testo(valore: Any) -> str | None:
    if valore is None:
        return None
    if isinstance(valore, bytes):
        valore = valore.decode("utf-8", "ignore")
    pulito = str(valore).strip().strip("\x00")
    return pulito or None


def _quando(valore: Any) -> datetime | None:
    """La data EXIF è scritta come `2021:05:26 20:35:25`, non in ISO."""
    testo = _testo(valore)
    if not testo:
        return None
    try:
        return datetime.strptime(testo, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def _numero(valore: Any) -> float | None:
    """Un valore EXIF razionale, comunque sia arrivato.

    Pillow di solito restituisce un `IFDRational`, ma a seconda di come il file
    e' stato scritto puo' arrivare una coppia `(numeratore, denominatore)`, o
    un numero gia' pronto. `Fraction` da solo rifiuta la coppia.
    """
    if valore is None:
        return None
    try:
        if isinstance(valore, tuple) and len(valore) == 2:
            numeratore, denominatore = valore
            return float(numeratore) / float(denominatore) if denominatore else None
        return float(Fraction(valore))
    except TypeError, ValueError, ZeroDivisionError:
        return None


def _gradi(coordinata: Any, riferimento: Any) -> float | None:
    """Converte gradi, primi e secondi nel numero decimale usato dalle mappe."""
    try:
        parti = [_numero(v) for v in coordinata]
    except TypeError:
        return None
    if len(parti) != 3 or any(p is None for p in parti):
        return None
    gradi, primi, secondi = (p for p in parti if p is not None)
    valore = gradi + primi / 60 + secondi / 3600
    # Sud e Ovest si scrivono come lettera, non come segno.
    if _testo(riferimento) in {"S", "W"}:
        valore = -valore
    return round(valore, 6)


def _frazione(valore: Any) -> str | None:
    """Il tempo di posa si legge come `1/250`, non come `0.004`."""
    numero = _numero(valore)
    if numero is None or numero <= 0:
        return None
    if numero >= 1:
        return f"{numero:g} s"
    return f"1/{round(1 / numero)} s"


def leggi(percorso: Path) -> DatiScatto:
    """Legge i dati di scatto. Sincrona: la chiama un thread separato.

    Non solleva: una foto senza EXIF, o con EXIF illeggibili, è un caso
    normalissimo — le immagini modificate o esportate spesso li perdono. Si
    restituisce quello che c'è.
    """
    try:
        with Image.open(percorso) as immagine:
            larghezza, altezza = immagine.size
            grezzi = immagine.getexif()
            dettagli = grezzi.get_ifd(_CAMPI.get("ExifOffset", 0x8769)) if grezzi else {}
            posizione = grezzi.get_ifd(_CAMPI.get("GPSInfo", 0x8825)) if grezzi else {}
    except UnidentifiedImageError, OSError, ValueError:
        return DatiScatto()

    def dettaglio(nome: str) -> Any:
        return dettagli.get(_CAMPI.get(nome, -1))

    latitudine = longitudine = None
    if posizione:
        latitudine = _gradi(
            posizione.get(_GPS.get("GPSLatitude", -1)),
            posizione.get(_GPS.get("GPSLatitudeRef", -1)),
        )
        longitudine = _gradi(
            posizione.get(_GPS.get("GPSLongitude", -1)),
            posizione.get(_GPS.get("GPSLongitudeRef", -1)),
        )

    diaframma = dettaglio("FNumber")
    focale = dettaglio("FocalLength")
    iso = dettaglio("ISOSpeedRatings")

    return DatiScatto(
        # `DateTimeOriginal` è il momento dello scatto; `DateTime` è l'ultima
        # modifica del file e cambia a ogni ritocco.
        scattata=_quando(dettaglio("DateTimeOriginal")) or _quando(grezzi.get(0x0132)),
        fotocamera=" ".join(
            p for p in (_testo(grezzi.get(0x010F)), _testo(grezzi.get(0x0110))) if p
        )
        or None,
        obiettivo=_testo(dettaglio("LensModel")),
        tempo=_frazione(dettaglio("ExposureTime")),
        diaframma=f"f/{_numero(diaframma):g}" if _numero(diaframma) else None,
        iso=int(iso) if isinstance(iso, int | float) else None,
        focale=f"{_numero(focale):g} mm" if _numero(focale) else None,
        latitudine=latitudine,
        longitudine=longitudine,
        larghezza=larghezza,
        altezza=altezza,
    )
