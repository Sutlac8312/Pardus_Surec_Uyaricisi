import os
import time

SAYFA_BOYUTU = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096


def _dosya_oku(yol):
    with open(yol, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


class Olcumcu:
    def __init__(self, proc_kok="/proc", sayfa_boyutu=SAYFA_BOYUTU):
        self.proc_kok = proc_kok
        self.sayfa_boyutu = sayfa_boyutu
        self._onceki_sistem = None
        self._onceki_surec = {}

    def _yol(self, *parcalar):
        return os.path.join(self.proc_kok, *map(str, parcalar))

    def sistem_cpu_zamani(self):
        for satir in _dosya_oku(self._yol("stat")).splitlines():
            if satir.startswith("cpu "):
                degerler = [int(x) for x in satir.split()[1:9]]
                degerler += [0] * (8 - len(degerler))
                bosta = degerler[3] + degerler[4]
                return sum(degerler), bosta
        raise ValueError("/proc/stat içinde cpu satırı yok")

    def bellek_bilgisi(self):
        alanlar = {}
        for satir in _dosya_oku(self._yol("meminfo")).splitlines():
            ad, _, deger = satir.partition(":")
            parca = deger.split()
            if parca:
                alanlar[ad.strip()] = int(parca[0]) * 1024
        toplam = alanlar["MemTotal"]
        if "MemAvailable" in alanlar:
            kullanilabilir = alanlar["MemAvailable"]
        else:
            kullanilabilir = sum(alanlar.get(k, 0) for k in ("MemFree", "Buffers", "Cached"))
        return toplam, kullanilabilir

    def pid_listesi(self):
        try:
            return sorted(int(ad) for ad in os.listdir(self.proc_kok) if ad.isdigit())
        except OSError:
            return []

    def surec_bilgisi(self, pid):
        icerik = _dosya_oku(self._yol(pid, "stat"))
        ac = icerik.index("(")
        kapa = icerik.rindex(")")
        ad = icerik[ac + 1:kapa]
        alanlar = icerik[kapa + 2:].split()
        cpu_zamani = int(alanlar[11]) + int(alanlar[12])
        baslangic = int(alanlar[19])
        rss_bayt = max(int(alanlar[21]), 0) * self.sayfa_boyutu
        return {"pid": pid, "ad": ad, "cpu_zamani": cpu_zamani,
                "baslangic": baslangic, "rss_bayt": rss_bayt}

    def olcum_al(self):
        sistem_toplam, sistem_bosta = self.sistem_cpu_zamani()
        bellek_toplam, bellek_kullanilabilir = self.bellek_bilgisi()

        sistem_cpu = None
        toplam_fark = None
        if self._onceki_sistem is not None:
            toplam_fark = sistem_toplam - self._onceki_sistem[0]
            bosta_fark = sistem_bosta - self._onceki_sistem[1]
            if toplam_fark > 0:
                sistem_cpu = round(100.0 * (toplam_fark - bosta_fark) / toplam_fark, 1)
        self._onceki_sistem = (sistem_toplam, sistem_bosta)

        ram_yuzde = round(100.0 * (bellek_toplam - bellek_kullanilabilir) / bellek_toplam, 1)

        surecler = []
        yeni_onceki = {}
        for pid in self.pid_listesi():
            try:
                bilgi = self.surec_bilgisi(pid)
            except (OSError, ValueError, IndexError):
                continue
            anahtar = (pid, bilgi["baslangic"])
            yeni_onceki[anahtar] = bilgi["cpu_zamani"]
            cpu_yuzde = None
            if toplam_fark and anahtar in self._onceki_surec:
                fark = bilgi["cpu_zamani"] - self._onceki_surec[anahtar]
                cpu_yuzde = round(max(0.0, min(100.0, 100.0 * fark / toplam_fark)), 1)
            surecler.append({
                "pid": pid,
                "ad": bilgi["ad"],
                "cpu_yuzde": cpu_yuzde,
                "ram_yuzde": round(100.0 * bilgi["rss_bayt"] / bellek_toplam, 1),
            })
        self._onceki_surec = yeni_onceki

        return {
            "zaman": time.time(),
            "cpu_yuzde": sistem_cpu,
            "ram_yuzde": ram_yuzde,
            "surecler": surecler,
        }


if __name__ == "__main__":
    olcumcu = Olcumcu()
    olcumcu.olcum_al()
    time.sleep(1)
    sonuc = olcumcu.olcum_al()
    print("CPU %:", sonuc["cpu_yuzde"], "| RAM %:", sonuc["ram_yuzde"])
    enler = sorted(sonuc["surecler"], key=lambda s: s["cpu_yuzde"] or 0, reverse=True)[:5]
    for s in enler:
        print(s["pid"], s["ad"], s["cpu_yuzde"], s["ram_yuzde"])
