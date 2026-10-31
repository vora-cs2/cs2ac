# CS2AC derlemesi (VORA Topluluk)

[karola3vax/CS2AC](https://github.com/karola3vax/CS2AC) `v1.0.14`'ün güncel CS2 SDK'sı ve güncel Metamod:Source ile yeniden derlenmiş
hâli. Yazar açık kaynak sürümü 2026-10-06'da bıraktı; bu depo onu bugünkü oyunda çalışır tutar.

- **Ne değişti:** `yamalar/cs2ac-s2sdk.patch`
  - SourceHook yerine KHook (Metamod 2.0 git1483 ve sonrası);
  - eski hl2sdk yerine [alliedmodders/s2sdk](https://github.com/alliedmodders/s2sdk) `cs2` dalı: CS2AC'nin kendi
    `CServerSideClient` ve `CGameResourceService` kopyaları kaldırıldı, SDK'nınkiler kullanılıyor;
  - hareket yapıları [CS2KZ](https://github.com/KZGlobalTeam/cs2kz-metamod)'nin güncel `datatypes.h`'ından;
  - `CSteamGameServerAPIContext` yerine Steam'in global erişimcileri.
- **Gamedata:** `gamedata/cs2ac.games.txt`. İmzalar CS2KZ'den, offset'ler CS2KZ ve SwiftlyS2'den alındı.
- **Derleme:** `.github/workflows/derle.yml` 6 saatte bir girdileri denetler: `s2sdk` `cs2` dalının ucu, Metamod'un son sürümü
  (`mmsdrop`), yama ve gamedata. Biri değişince Windows ve Linux için derler ve `derleme-<anahtar>` adıyla yayınlar.
  Yerelde: `python derle.py --platform windows` (VS C++ araçları + Python) ya da `--platform linux` (Docker).
- **Kurulum:** sunucu paneli en son yayının `surum.json`'unu okur. İkilinin SHA-256'sını doğrular ve sunucu boşken kurar.
  Eklenti yüklenmezse ya da kurulumdan sonraki 24 saatte sunucu CS2AC'li çökerse önceki derlemeye döner.

Lisans: AGPL-3.0 (`LICENSE`, CS2AC'ninki). Bu depo, sunucuda çalışan değiştirilmiş kaynağın kendisidir: `v1.0.14` + `yamalar/`.
