# own-voice-dub

**Kendi videonu, kendi sesinle başka bir dile çevir. Ücretsiz, kendi bilgisayarında.**
Türkçe videonun İngilizce (ya da İspanyolca, Fransızca, Almanca, Rusça, Japonca, Çince) ses parçasını çıkarır;
YouTube Studio → Diller → Dublaj'a yüklersin, izleyici ayarlardan dili seçer.

[English below](#english)

> **Uyarı (13 Kasım 2026):** Demucs'un modelini indirdiği Meta sunucusunun sertifikası 11 Kasım'da doldu; ilk kurulumda
> `certificate has expired` hatası alırsan modeli bu reponun Releases sayfasından al ([Demucs modeli inmezse](#demucs-modeli-inmezse)).
> Model dosyasını Meta'nın kendi sunucusundan indirip SHA-256'sıyla değiştirmeden koyduk; Meta model için ayrı bir lisans yazmıyor,
> Demucs reposu MIT. Sertifika yenilenince Meta'nın sunucusu yine kendiliğinden çalışır.
> **Warning:** Meta's Demucs model server certificate expired on 11 Nov 2026. If the first run fails with `certificate has expired`,
> take the unmodified model file from this repo's Releases and check its SHA-256 (see the English section).


## Nasıl çalışıyor

1. **Cümleleri bulur** (Whisper): videonun her cümlesi, başladığı ve bittiği saniyeyle.
2. **Çeviri** (Claude Code): her cümlenin çevirisini sen ya da Claude Code yazar; Türkçe cümleden uzun olmaz.
3. **Müziği ayırır** (Demucs): videonun sesinden konuşmayı çıkarır, müzik ve efekt kalır.
4. **Ana dili o dil olan bir anlatıcı okur** (VoxCPM2): aksan anlatıcının olur.
5. **Sesi senin sesine çevirir** (Chatterbox): ses rengi senin olur. 10–30 saniyelik bir kayıt yeter.
6. **Dinleyip kontrol eder** (Whisper): önemli kelimeler duyulmazsa cümle yeniden üretilir, en çok 3 kez.
7. **Yerine sığdırır**: her cümle Türkçe cümlenin yerine oturur; boşluklar kısalır, gerekirse konuşma en çok %15 hızlanır.
   Hâlâ sığmayan cümleyi söyler: o çeviriyi kısalt.
8. **Karıştırır**: her cümle aynı ses seviyesine gelir, müziğin üstüne konur, bütün parça videonun ses düzeyine eşitlenir.

Çıktı: `video.en-dub.m4a` (Studio'ya yüklenecek) ve `video.en.srt` (aynı dilde altyazı).

## Gerekenler

- Apple Silicon Mac (M1 ve sonrası, 16 GB önerilir) ya da Nvidia ekran kartlı Windows PC. İkisinde de baştan sona denendi
  (M4 16 GB: 40 sn'lik video 4 dk 25 sn; RTX 3070 8 GB: 93 sn). Linux'ta denenmedi.
- ~8 GB boş yer (modeller ve ortam)
- ffmpeg, whisper.cpp (`whisper-cli`) ve Whisper `large-v3-turbo` modeli
- [voxcpm2-turkce-ses-tasarimi](https://github.com/alexturkey/voxcpm2-turkce-ses-tasarimi) (VoxCPM2 + hazır anlatıcı sesleri)
- Python 3.11 ortamında `chatterbox-tts==0.1.7`, `demucs==4.0.1` ve `setuptools<81` (bu sürümlerle denendi)
- Windows / Nvidia'da önce torch'un CUDA sürümü: `torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124`,
  sonra `chatterbox-tts` (yoksa ekran kartı kullanılmaz)

### Demucs modeli inmezse

Demucs ilk çalıştırmada modelini (`955717e8-8726e21a.th`, 84 MB) Meta'nın sunucusundan indirir. O sunucunun sertifikası
11 Kasım 2026'da doldu; yenilenene kadar indirme `certificate has expired` hatasıyla düşer. Sertifika kontrolünü kapatma.
Bu reponun Releases sayfasındaki aynı dosyayı indir, SHA-256'sını kontrol et ve torch'un klasörüne koy:

```
SHA-256: 8726e21a993978c7ba086d3872e7608d7d5bfca646ca4aca459ffda844faa8b4
Mac / Linux: ~/.cache/torch/hub/checkpoints/955717e8-8726e21a.th
Windows:     %USERPROFILE%\.cache\torch\hub\checkpoints\955717e8-8726e21a.th
```
Kontrol: Mac'te `shasum -a 256 <dosya>`, Windows'ta `certutil -hashfile <dosya> SHA256`. Kod farklıysa dosyayı kullanma.

## Kurulum: Claude Code'a yapıştır

```
Bu klasördeki own-voice-dub aracını bu bilgisayara kur. README.md'deki "Gerekenler" listesine göre önce neyin
kurulu olduğunu kontrol et, eksikleri ve kaç GB indireceğini bana listele, ben onaylamadan hiçbir şey indirme ya da
kurma. Onaylarsam: ffmpeg ve whisper-cpp'yi kur, Whisper large-v3-turbo modelini indir,
voxcpm2-turkce-ses-tasarimi'ni kendi AGENTS.md'sine göre kur, Python 3.11 ile bir sanal ortam açıp chatterbox-tts==0.1.7,
demucs==4.0.1 ve setuptools<81'i kur (Nvidia'da önce "Gerekenler"deki CUDA'lı torch'u), config.example.json'u config.json
olarak kopyalayıp yolları doldur. Demucs modeli sertifika hatasıyla inmezse "Demucs modeli inmezse" bölümünü uygula,
sertifika kontrolünü kapatma. Sonunda kısa bir deneme yap ve sonucu söyle.
```

## Kullanım

```bash
python dub.py prepare video.mp4 --from tr
```
`video.dub.json` çıkar: her cümle, zamanıyla. Sonra Claude Code'a şunu yaz:

```
video.dub.json'daki her cümleye "en" alanı ekle: o cümlenin İngilizcesi. Kurallar: her çeviri, söylendiğinde Türkçe
cümleden uzun olmasın; kesme işareti kullanma ("it's" değil "it is"); her Türkçe cümle tek bir İngilizce cümle olsun,
ortasına nokta, soru işareti, iki nokta ya da noktalı virgül koyma; marka adlarını olduğu gibi bırak. Sayılar İngilizcede rakamla kalabilir; başka bir dilde sayıyı yazıyla yaz.
```

Sonra:
```bash
python dub.py run video.mp4 --voice sesim.wav --lang en
```

YouTube Studio → Diller → Dil ekle → Dublaj → Ekle → dosyayı seç. O dilde otomatik dublaj varsa önce onu sil.

## Öğrendiklerimiz (neden böyle yapıyor)

[KURALLAR.md](KURALLAR.md): kendi kanalımda 10 videoyu böyle dublajlarken ve 4 ücretsiz modeli ElevenLabs'le yarıştırırken çıkan 12 ders.

## Lisanslar

Bu repodaki kod MIT. Kullandığı araçların kendi lisansları var: VoxCPM2 ve voxcpm2-turkce-ses-tasarimi Apache-2.0,
Chatterbox MIT, Demucs MIT (Demucs reposunun lisansı; model ağırlıkları için ayrı bir lisans yazmıyor), whisper.cpp MIT. Yalnız kendi sesini ya da sahibinin açık izni olan bir sesi kullan.
YouTube'un [kendi sayfasına](https://support.google.com/youtube/answer/14328491) göre kendi sesini klonlayıp dublaj yapmak
"yapay zekâ kullanımı" olarak bildirmen gerekmeyen küçük değişikliklerden; başka birine söylemediği bir şeyi söyletmek bildirilir.

---

## English

**Dub your own video into another language, in your own voice, free, on your own computer.**
Turns a video into an English (or Spanish, French, German, Russian, Japanese, Chinese) audio track you upload in
YouTube Studio → Languages → Dub.

How: Whisper finds the sentences and their times; you or Claude Code translate each one (no longer than the original);
Demucs removes the voice and keeps the music; a native narrator reads each sentence (VoxCPM2); Chatterbox turns it into
your voice from a 10–30 s recording; Whisper checks every sentence and converts it again if a key word is missing;
each sentence is fitted into the original's slot (up to 15% faster), levelled and mixed over the music.

```bash
python dub.py prepare video.mp4 --from tr
# add an "en" field to every sentence in video.dub.json (see the translation prompt above)
python dub.py run video.mp4 --voice my-voice.wav --lang en
```

Install: paste the Turkish install prompt above into Claude Code (it works in any language), or follow "Gerekenler".
Tested end to end on an M4 Mac (16 GB) and a Windows PC with an RTX 3070 (8 GB); not tested on Linux. Pinned versions:
`chatterbox-tts==0.1.7`, `demucs==4.0.1`, `setuptools<81`; on Nvidia install the CUDA build of torch 2.6.0 (cu124) first.
If the Demucs model download fails with `certificate has expired` (Meta's server certificate expired on 11 Nov 2026), take
`955717e8-8726e21a.th` from this repo's Releases, check SHA-256 `8726e21a993978c7ba086d3872e7608d7d5bfca646ca4aca459ffda844faa8b4` and put it in
`~/.cache/torch/hub/checkpoints/` (Windows: `%USERPROFILE%\.cache\torch\hub\checkpoints\`). Never turn off certificate checks.

Code MIT; VoxCPM2 Apache-2.0, Chatterbox MIT, Demucs MIT (the Demucs repo's licence; it states no separate licence for the model weights), whisper.cpp MIT. Only use your own voice or one you
have explicit permission for. YouTube's [policy](https://support.google.com/youtube/answer/14328491) lists cloning your own
voice for dubs as a change you do not have to disclose; making a real person say something they did not say must be disclosed.
