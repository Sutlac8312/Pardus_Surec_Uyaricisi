# Pardus Süreç Uyarıcısı

BİL461 kapsamında geliştirilen bu komut satırı aracı, Pardus’ta sistemin CPU ve RAM kullanımını izler. Her ölçümde CPU ve RAM’i en çok kullanan süreçleri ayrı listelerde PID, süreç adı ve kullanım yüzdeleriyle gösterir. Belirlenen eşik art arda aşıldığında terminalde Türkçe uyarı gösterir ve uyarıyı tarih ve saatle bir metin dosyasına ekler.

## Çalıştırma

Pardus’ta Python 3 ile çalıştırılır. `surec_uyarici.py` ve ölçüm verilerini sağlayan `olcum.py` aynı dizinde olmalıdır. Repo dizininde çalıştırın.

```bash
python3 surec_uyarici.py
```

Örneğin her saniye ölçüm alıp CPU kullanımı %80’i veya RAM kullanımı %85’i art arda iki ölçümde aşınca uyarı vermek için şu komutu kullanın.

```bash
python3 surec_uyarici.py --aralik 1 --cpu-esik 80 --ram-esik 85 --ardisik 2
```

İzlemeyi durdurmak için `Ctrl+C` tuşlarına basın. CPU yüzdesi hesaplanana kadar terminalde `-` görünür. CPU ve RAM eşikleri ayrı izlenir. Her kesintisiz eşik aşımında bir kez uyarı verilir ve kullanım eşik değerine döndüğünde veya altına indiğinde sayaç sıfırlanır.

## Komut satırı seçenekleri

| Seçenek | Varsayılan | Açıklama |
| --- | --- | --- |
| `--aralik` | `2.0` | Ölçümler arasındaki bekleme süresi (saniye) |
| `--cpu-esik` | `85.0` | Sistem CPU kullanım eşiği (%) |
| `--ram-esik` | `85.0` | Sistem RAM kullanım eşiği (%) |
| `--ardisik` | `3` | Uyarı için gereken ardışık eşik aşımı sayısı |
| `--surec-sayisi` | `5` | Her listede gösterilecek en fazla süreç sayısı |
| `--kayit-dosyasi` | `surec_uyarilari.log` | Uyarıların ekleneceği dosya |
| `-h`, `--help` | | Yardım ekranını gösterir |

## Proje ekibi

- **Ömer Bulunmaz** — Terminal arayüzü, süreç listesi, eşik uyarıları ve kayıt.
- **Selim Şeker** — `/proc` verilerinin okunması ve CPU/RAM ölçümleri.
