# own-voice-dub

**Kendi videonu, kendi sesinle başka bir dile çevir. Ücretsiz, kendi bilgisayarında.**
Türkçe videonun İngilizce (ya da İspanyolca, Fransızca, Almanca, Rusça, Japonca, Çince) ses parçasını çıkarır;
YouTube Studio → Diller → Dublaj'a yüklersin, izleyici ayarlardan dili seçer.

[English below](#english)

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

- Apple Silicon Mac (M1 ve sonrası, 16 GB önerilir) ya da Nvidia ekran kartlı Windows / Linux PC
- ~8 GB boş yer (modeller ve ortam)
- ffmpeg, whisper.cpp (`whisper-cli`) ve Whisper `large-v3-turbo` modeli
- [voxcpm2-turkce-ses-tasarimi](https://github.com/alexturkey/voxcpm2-turkce-ses-tasarimi) (VoxCPM2 + hazır anlatıcı sesleri)
- Python 3.11 ortamında `chatterbox-tts` ve `demucs`

## Kurulum: Claude Code'a yapıştır

```
Bu klasördeki own-voice-dub aracını bu bilgisayara kur. README.md'deki "Gerekenler" listesine göre önce neyin
kurulu olduğunu kontrol et, eksikleri ve kaç GB indireceğini bana listele, ben onaylamadan hiçbir şey indirme ya da
kurma. Onaylarsam: ffmpeg ve whisper-cpp'yi kur, Whisper large-v3-turbo modelini indir,
voxcpm2-turkce-ses-tasarimi'ni kendi AGENTS.md'sine göre kur, Python 3.11 ile bir sanal ortam açıp chatterbox-tts ve
demucs'u kur, config.example.json'u config.json olarak kopyalayıp yolları doldur. Sonunda kısa bir deneme yap ve
sonucu söyle.
```

## Kullanım

```bash
python dub.py prepare video.mp4 --from tr
```
`video.dub.json` çıkar: her cümle, zamanıyla. Sonra Claude Code'a şunu yaz:

```
video.dub.json'daki her cümleye "en" alanı ekle: o cümlenin İngilizcesi. Kurallar: her çeviri, söylendiğinde Türkçe
cümleden uzun olmasın; kesme işareti kullanma ("it's" değil "it is"); bir cümleyi iki noktayla ya da noktalı virgülle
bölme; marka adlarını olduğu gibi bırak. Sayılar İngilizcede rakamla kalabilir; başka bir dilde sayıyı yazıyla yaz.
```

Sonra:
```bash
python dub.py run video.mp4 --voice sesim.wav --lang en
```

YouTube Studio → Diller → Dil ekle → Dublaj → Ekle → dosyayı seç. O dilde otomatik dublaj varsa önce onu sil.

## Öğrendiklerimiz (neden böyle yapıyor)

[KURALLAR.md](KURALLAR.md): kendi kanalımda 10 videoyu böyle dublajlarken çıkan dersler.

## Lisanslar

Bu repodaki kod MIT. Kullandığı araçların kendi lisansları var: VoxCPM2 ve voxcpm2-turkce-ses-tasarimi Apache-2.0,
Chatterbox MIT, Demucs MIT, whisper.cpp MIT. Yalnız kendi sesini ya da sahibinin açık izni olan bir sesi kullan;
ürettiğin sesi yapay zekâ ile üretildi diye etiketle (YouTube'da "değiştirilmiş ya da yapay içerik").

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
Code MIT; VoxCPM2 Apache-2.0, Chatterbox MIT, Demucs MIT, whisper.cpp MIT. Only use your own voice or one you have
explicit permission for, and label the result as AI-generated.
