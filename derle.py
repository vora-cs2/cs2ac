#!/usr/bin/env python3
"""CS2AC'yi (karola3vax/CS2AC v1.0.14, AGPL-3.0) güncel CS2 SDK'sı (alliedmodders/s2sdk, dal cs2) ve sunucuların indirdiği
Metamod:Source sürümüyle yeniden derler.

  python derle.py --girdi                 # derlemeden, kullanılacak sürümleri ve anahtarı JSON olarak yazar
  python derle.py --platform windows      # derler; cikti/cs2ac-windows.zip + cikti/surum-windows.json
  python derle.py --platform linux --s2sdk <sha> --metamod-build <n>

Anahtar, girdilerin (SDK commit'i, Metamod derleme numarası, yama ve gamedata) özetidir: aynı anahtar aynı derleme demektir.
Metamod'un derleme numarası (mmsdrop "git1483") metamod-source deposunun commit sayısıdır (1483 = 170058a, 2026-10-31 doğrulandı).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone

KOK = os.path.dirname(os.path.abspath(__file__))
CS2AC_DEPO = 'https://github.com/karola3vax/CS2AC'
CS2AC_ETIKET = 'v1.0.14'
S2SDK_DEPO = 'https://github.com/alliedmodders/s2sdk'
S2SDK_DAL = 'cs2'
MMS_DEPO = 'https://github.com/alliedmodders/metamod-source'
MMS_SON = 'https://mms.alliedmods.net/mmsdrop/2.0/mmsource-latest-windows'
YAMA = os.path.join(KOK, 'yamalar', 'cs2ac-s2sdk.patch')
GAMEDATA = os.path.join(KOK, 'gamedata', 'cs2ac.games.txt')


def calistir(komut, cwd=None, cikti=False):
    print('>', ' '.join(komut), flush=True)
    # AMBuild derleyici çıktısını yazarken, çıktı dosyaya/boruya gidince (cp1252) Türkçe MSVC iletilerinde düşüyordu.
    ortam = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    if cikti:
        return subprocess.run(komut, cwd=cwd, check=True, capture_output=True, text=True, env=ortam).stdout
    subprocess.run(komut, cwd=cwd, check=True, env=ortam)
    return ''


def sil(yol):
    # git nesneleri salt okunur: Windows'ta önce yazılabilir yap.
    def yazilabilir(islev, y, _):
        os.chmod(y, 0o700)
        islev(y)
    shutil.rmtree(yol, onerror=yazilabilir)


def ozet(*yollar):
    h = hashlib.sha256()
    for y in yollar:
        with open(y, 'rb') as f:
            # Satır sonundan bağımsız (Windows checkout'u CRLF yapabilir).
            h.update(f.read().replace(b'\r\n', b'\n'))
    return h.hexdigest()


def s2sdk_son():
    satir = calistir(['git', 'ls-remote', S2SDK_DEPO, f'refs/heads/{S2SDK_DAL}'], cikti=True).split()
    return satir[0]


def mms_son_derleme():
    # Varsayılan Python-urllib kimliğine 403 veriyor.
    istek = urllib.request.Request(MMS_SON, headers={'User-Agent': 'cs2ac-derleme'})
    with urllib.request.urlopen(istek, timeout=30) as yanit:
        ad = yanit.read().decode().strip()
    m = re.search(r'git(\d+)', ad)
    if not m:
        raise SystemExit(f'Metamod sürüm adı okunamadı: {ad!r}')
    return int(m.group(1))


def girdiler(args):
    g = {
        'cs2ac': CS2AC_ETIKET,
        's2sdk': args.s2sdk or s2sdk_son(),
        'metamod_build': args.metamod_build or mms_son_derleme(),
        'yama': ozet(YAMA),
        'gamedata': ozet(GAMEDATA),
        'betik': ozet(os.path.abspath(__file__)),
    }
    anahtar = hashlib.sha256(json.dumps(g, sort_keys=True).encode()).hexdigest()[:12]
    g['anahtar'] = anahtar
    return g


def depo_commit(hedef, depo, commit):
    os.makedirs(hedef, exist_ok=True)
    calistir(['git', 'init', '-q'], cwd=hedef)
    calistir(['git', 'remote', 'add', 'origin', depo], cwd=hedef)
    calistir(['git', 'fetch', '-q', '--depth', '1', 'origin', commit], cwd=hedef)
    calistir(['git', 'checkout', '-q', 'FETCH_HEAD'], cwd=hedef)


def metamod(hedef, derleme):
    calistir(['git', 'clone', '-q', '--filter=blob:none', '--no-checkout', MMS_DEPO, hedef])
    commitler = calistir(['git', 'rev-list', '--reverse', 'origin/HEAD'], cwd=hedef, cikti=True).split()
    if derleme > len(commitler):
        raise SystemExit(f'Metamod derleme {derleme} depoda yok (commit sayısı {len(commitler)}).')
    commit = commitler[derleme - 1]
    calistir(['git', 'checkout', '-q', commit], cwd=hedef)
    calistir(['git', 'submodule', 'update', '-q', '--init', '--recursive', '--depth', '1'], cwd=hedef)
    return commit


def derle(args):
    g = girdiler(args)
    calisma = os.path.abspath(args.calisma)
    if os.path.exists(calisma):
        sil(calisma)
    kaynak = os.path.join(calisma, 'cs2ac')
    calistir(['git', '-c', 'core.autocrlf=false', 'clone', '-q', '--depth', '1', '--branch', CS2AC_ETIKET, CS2AC_DEPO, kaynak])
    # .git kalırsa bootstrap betikleri alt modülleri CS2AC'nin eski sabit sürümlerine geri çeker.
    sil(os.path.join(kaynak, '.git'))
    for ad in ('hl2sdk-cs2', 'metamod-source'):
        yol = os.path.join(kaynak, ad)
        if os.path.exists(yol):
            sil(yol)
    depo_commit(os.path.join(kaynak, 'hl2sdk-cs2'), S2SDK_DEPO, g['s2sdk'])
    g['metamod_commit'] = metamod(os.path.join(kaynak, 'metamod-source'), g['metamod_build'])
    calistir(['git', 'apply', '--whitespace=nowarn', YAMA], cwd=kaynak)
    shutil.copyfile(GAMEDATA, os.path.join(kaynak, 'gamedata', 'cs2ac.games.txt'))

    if args.platform == 'windows':
        calistir(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'build-windows.ps1'], cwd=kaynak)
        ikili = os.path.join('addons', 'cs2ac', 'bin', 'win64', 'cs2ac.dll')
        paket = os.path.join(kaynak, 'build-windows-release', 'package', 'game', 'csgo')
    else:
        calistir(['bash', 'build-linux.sh'], cwd=kaynak)
        ikili = os.path.join('addons', 'cs2ac', 'bin', 'linuxsteamrt64', 'cs2ac.so')
        paket = os.path.join(kaynak, 'build-linux-release', 'package', 'game', 'csgo')

    tam = os.path.join(paket, ikili)
    if not os.path.isfile(tam):
        raise SystemExit(f'Derleme {ikili} üretmedi.')
    g['platform'] = args.platform
    g['dosya'] = ikili.replace(os.sep, '/')
    g['sha256'] = hashlib.sha256(open(tam, 'rb').read()).hexdigest()
    g['tarih'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    os.makedirs(args.cikti, exist_ok=True)
    with zipfile.ZipFile(os.path.join(args.cikti, f'cs2ac-{args.platform}.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(tam, g['dosya'])
        z.writestr('addons/cs2ac/surum.json', json.dumps(g, indent=2, ensure_ascii=False))
    with open(os.path.join(args.cikti, f'surum-{args.platform}.json'), 'w', encoding='utf-8') as f:
        json.dump(g, f, indent=2, ensure_ascii=False)
    print(json.dumps(g, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--girdi', action='store_true', help='derlemeden girdileri ve anahtarı yaz')
    p.add_argument('--platform', choices=('windows', 'linux'))
    p.add_argument('--s2sdk', help='s2sdk commit (varsayılan: cs2 dalının ucu)')
    p.add_argument('--metamod-build', type=int, help='Metamod derleme numarası (varsayılan: mmsdrop son sürüm)')
    p.add_argument('--calisma', default='calisma')
    p.add_argument('--cikti', default='cikti')
    args = p.parse_args()
    if args.girdi:
        g = girdiler(args)
        print(json.dumps(g, ensure_ascii=False))
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as f:
                for k in ('anahtar', 's2sdk', 'metamod_build'):
                    f.write(f'{k}={g[k]}\n')
        return
    if not args.platform:
        p.error('--platform ya da --girdi gerekli')
    derle(args)


if __name__ == '__main__':
    sys.exit(main())
