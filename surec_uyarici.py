"""Pardus için CPU ve RAM izleme, eşik uyarıları ve metin kaydı.

Ölçüm katmanı, olcum.py içinde olcum_al() metodu olan bir Olcumcu sınıfı
sağlar. Metot aşağıdaki Olcum şemasında bir sözlük döndürür. Ardışık CPU
ölçümleri için aynı Olcumcu örneği kullanılır ve ilk CPU yüzdesi None olabilir.
"""

import argparse
import sys
from datetime import datetime
from math import isfinite
from pathlib import Path
from time import sleep
from typing import List, Literal, Optional, TypedDict


class Surec(TypedDict):
    pid: int
    ad: str
    cpu_yuzde: Optional[float]
    ram_yuzde: float


class Olcum(TypedDict):
    cpu_yuzde: Optional[float]
    ram_yuzde: float
    surecler: List[Surec]


def pozitif_saniye(metin: str) -> float:
    saniye = float(metin)
    if not isfinite(saniye) or saniye <= 0:
        raise argparse.ArgumentTypeError("Aralık sıfırdan büyük ve sonlu olmalıdır.")
    return saniye


def yuzde(metin: str) -> float:
    deger = float(metin)
    if not 0 <= deger <= 100:
        raise argparse.ArgumentTypeError("Eşik 0 ile 100 arasında olmalıdır.")
    return deger


def pozitif_tamsayi(metin: str) -> int:
    sayi = int(metin)
    if sayi < 1:
        raise argparse.ArgumentTypeError("Sayı en az 1 olmalıdır.")
    return sayi


def secenekleri_oku() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pardus'ta CPU ve RAM kullanımını izler, eşik aşımında uyarı verir.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--aralik", type=pozitif_saniye, default=2.0, metavar="SANİYE",
        help="Ölçümler arasındaki bekleme süresi",
    )
    parser.add_argument(
        "--cpu-esik", type=yuzde, default=85.0, metavar="YÜZDE",
        help="Sistem CPU kullanım eşiği",
    )
    parser.add_argument(
        "--ram-esik", type=yuzde, default=85.0, metavar="YÜZDE",
        help="Sistem RAM kullanım eşiği",
    )
    parser.add_argument(
        "--ardisik", type=pozitif_tamsayi, default=3, metavar="SAYI",
        help="Uyarı için gereken ardışık eşik aşımı sayısı",
    )
    parser.add_argument(
        "--surec-sayisi", type=pozitif_tamsayi, default=5, metavar="SAYI",
        help="Her listede gösterilecek en fazla süreç sayısı",
    )
    parser.add_argument(
        "--kayit-dosyasi", type=Path, default=Path("surec_uyarilari.log"), metavar="DOSYA",
        help="Uyarıların ekleneceği metin dosyası",
    )
    return parser.parse_args()


def yuzde_metni(deger: Optional[float]) -> str:
    return "-" if deger is None else f"%{deger:.1f}"


def surec_listesini_goster(
    surecler: List[Surec],
    alan: Literal["cpu_yuzde", "ram_yuzde"],
    kaynak: str,
    sinir: int,
) -> None:
    puanli_surecler = []
    for surec in surecler:
        kullanim = surec[alan]
        if kullanim is not None:
            puanli_surecler.append((kullanim, surec))
    puanli_surecler.sort(key=lambda kayit: kayit[0], reverse=True)

    print(f"\nEn çok {kaynak} kullanan süreçler")
    if not puanli_surecler:
        print("Gösterilecek ölçüm yok.")
        return

    print(f"{'PID':>7}  {'CPU':>8}  {'RAM':>8}  Süreç")
    for _, surec in puanli_surecler[:sinir]:
        ad = "".join(karakter if karakter.isprintable() else "?" for karakter in surec["ad"])
        print(
            f"{surec['pid']:>7}  {yuzde_metni(surec['cpu_yuzde']):>8}  "
            f"{yuzde_metni(surec['ram_yuzde']):>8}  {ad}"
        )


def main() -> int:
    secenekler = secenekleri_oku()
    try:
        from olcum import Olcumcu
    except ModuleNotFoundError as hata:
        if hata.name != "olcum":
            raise
        print(
            "Ölçüm modülü bulunamadı. olcum.py dosyasını programla aynı klasöre ekleyin.",
            file=sys.stderr,
        )
        return 1

    esikler = {"CPU": secenekler.cpu_esik, "RAM": secenekler.ram_esik}
    ardisik_asim = {"CPU": 0, "RAM": 0}

    try:
        olcumcu = Olcumcu()
        with secenekler.kayit_dosyasi.open("a", encoding="utf-8") as kayit:
            print("İzleme başladı. Durdurmak için Ctrl+C'ye basın.")
            while True:
                olcum: Olcum = olcumcu.olcum_al()
                zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                kullanimlar = {"CPU": olcum["cpu_yuzde"], "RAM": olcum["ram_yuzde"]}
                print(
                    f"\n{zaman}  CPU: {yuzde_metni(kullanimlar['CPU'])}  "
                    f"RAM: {yuzde_metni(kullanimlar['RAM'])}"
                )
                surec_listesini_goster(olcum["surecler"], "cpu_yuzde", "CPU", secenekler.surec_sayisi)
                surec_listesini_goster(olcum["surecler"], "ram_yuzde", "RAM", secenekler.surec_sayisi)

                for kaynak, kullanim in kullanimlar.items():
                    esik = esikler[kaynak]
                    if kullanim is None or kullanim <= esik:
                        ardisik_asim[kaynak] = 0
                        continue

                    ardisik_asim[kaynak] += 1
                    if ardisik_asim[kaynak] == secenekler.ardisik:
                        uyari = (
                            f"UYARI: Sistem {kaynak} kullanımı {yuzde_metni(kullanim)}. "
                            f"{yuzde_metni(esik)} eşiği {secenekler.ardisik} ölçümdür aşılıyor."
                        )
                        print(uyari, flush=True)
                        print(f"{zaman} {uyari}", file=kayit, flush=True)

                sleep(secenekler.aralik)
    except KeyboardInterrupt:
        print("\nİzleme durduruldu.")
        return 0
    except (OSError, OverflowError) as hata:
        print(f"İzleme hatası: {hata}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
