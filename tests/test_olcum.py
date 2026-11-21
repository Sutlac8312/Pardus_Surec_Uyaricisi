import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from olcum import Olcumcu


def stat_satiri(pid, ad, utime, stime, baslangic, rss):
    alanlar = ["S", "1", "1", "1", "0", "-1", "0", "0", "0", "0", "0",
               str(utime), str(stime), "0", "0", "20", "0", "1", "0",
               str(baslangic), "0", str(rss)] + ["0"] * 30
    return "%d (%s) %s\n" % (pid, ad, " ".join(alanlar))


class SahteProc:
    def __init__(self):
        self.kok = tempfile.mkdtemp()
        self.meminfo(1000000, 400000)

    def sistem(self, user, idle):
        with open(os.path.join(self.kok, "stat"), "w") as f:
            f.write("cpu  %d 0 0 %d 0 0 0 0 0 0\ncpu0 %d 0 0 %d 0 0 0 0 0 0\n" % (user, idle, user, idle))

    def meminfo(self, toplam_kb, kullanilabilir_kb):
        with open(os.path.join(self.kok, "meminfo"), "w") as f:
            f.write("MemTotal:       %d kB\nMemFree:        1 kB\nMemAvailable:   %d kB\n" % (toplam_kb, kullanilabilir_kb))

    def surec(self, pid, ad, utime, stime=0, baslangic=100, rss=0):
        klasor = os.path.join(self.kok, str(pid))
        os.makedirs(klasor, exist_ok=True)
        with open(os.path.join(klasor, "stat"), "w") as f:
            f.write(stat_satiri(pid, ad, utime, stime, baslangic, rss))

    def sil(self, pid):
        shutil.rmtree(os.path.join(self.kok, str(pid)))

    def temizle(self):
        shutil.rmtree(self.kok)


class OlcumTesti(unittest.TestCase):
    def setUp(self):
        self.proc = SahteProc()
        self.olcumcu = Olcumcu(proc_kok=self.proc.kok, sayfa_boyutu=4096)

    def tearDown(self):
        self.proc.temizle()

    def test_ilk_olcumde_cpu_bos(self):
        self.proc.sistem(100, 900)
        self.proc.surec(10, "python3", 50)
        sonuc = self.olcumcu.olcum_al()
        self.assertIsNone(sonuc["cpu_yuzde"])
        self.assertIsNone(sonuc["surecler"][0]["cpu_yuzde"])

    def test_ardisik_olcumden_cpu(self):
        self.proc.sistem(100, 900)
        self.proc.surec(10, "python3", 50)
        self.olcumcu.olcum_al()
        self.proc.sistem(160, 940)
        self.proc.surec(10, "python3", 80)
        sonuc = self.olcumcu.olcum_al()
        self.assertEqual(sonuc["cpu_yuzde"], 60.0)
        self.assertEqual(sonuc["surecler"][0]["cpu_yuzde"], 30.0)

    def test_ram_yuzdeleri(self):
        self.proc.sistem(100, 900)
        self.proc.surec(10, "firefox", 0, rss=25000)
        sonuc = self.olcumcu.olcum_al()
        self.assertEqual(sonuc["ram_yuzde"], 60.0)
        self.assertEqual(sonuc["surecler"][0]["ram_yuzde"], 10.0)

    def test_parantezli_ve_bosluklu_ad(self):
        self.proc.sistem(100, 900)
        self.proc.surec(11, "Web Content (x)", 5)
        sonuc = self.olcumcu.olcum_al()
        self.assertEqual(sonuc["surecler"][0]["ad"], "Web Content (x)")

    def test_kapanan_surec_atlanir(self):
        self.proc.sistem(100, 900)
        self.proc.surec(10, "a", 1)
        self.proc.surec(11, "b", 1)
        self.olcumcu.olcum_al()
        self.proc.sil(11)
        self.proc.sistem(200, 1000)
        sonuc = self.olcumcu.olcum_al()
        self.assertEqual([s["pid"] for s in sonuc["surecler"]], [10])

    def test_okunamayan_surec_atlanir(self):
        self.proc.sistem(100, 900)
        self.proc.surec(10, "a", 1)
        os.makedirs(os.path.join(self.proc.kok, "12"))
        with open(os.path.join(self.proc.kok, "12", "stat"), "w") as f:
            f.write("bozuk")
        sonuc = self.olcumcu.olcum_al()
        self.assertEqual([s["pid"] for s in sonuc["surecler"]], [10])

    def test_ayni_pid_yeni_surec(self):
        self.proc.sistem(100, 900)
        self.proc.surec(10, "eski", 500, baslangic=100)
        self.olcumcu.olcum_al()
        self.proc.surec(10, "yeni", 3, baslangic=200)
        self.proc.sistem(200, 1000)
        sonuc = self.olcumcu.olcum_al()
        self.assertIsNone(sonuc["surecler"][0]["cpu_yuzde"])


if __name__ == "__main__":
    unittest.main()
