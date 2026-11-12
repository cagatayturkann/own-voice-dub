# Öğrendiklerimiz

Kendi kanalımda (@cagatayturkann) 4 Kasım 2026'dan beri 10 videoyu (8 Short, 2 uzun video) kendi sesimle İngilizceye
dublajlarken ve 12 Kasım gecesi 4 ücretsiz modeli ElevenLabs'le yarıştırırken çıkan kurallar. Araç bunların çoğunu kendisi uyguluyor; metni yazarken senin bilmen gerekenler işaretli (✍).

1. **Sesini doğrudan İngilizce okutma.** Sesini kopyalayan model İngilizceyi senin ağzınla okuyor: bir modelde Türk aksanı,
   ötekinde Rus aksanı çıktı. Önce ana dili o dil olan bir anlatıcı okusun, sonra ses senin sesine çevrilsin.
2. **Her cümleyi dinlet.** Kontrol programı (Whisper) önemli kelimeleri duymazsa cümle yeniden üretilir. Bir videonun 52
   cümlesinin 48'i ilk seferde geçti. Kontrol de yanılır: "Claude Code"u "cloud code" diye yazar. Son kulak senin.
3. ✍ **Çeviri Türkçe cümleden uzun olmasın.** Dublaj Türkçe cümlenin yerine sığmak zorunda; yoksa söylenen ile görüntü kayar.
   Araç önce boşlukları kısaltır, sonra en çok %15 hızlandırır; yine sığmazsa söyler.
4. ✍ **Cümleyi bölme: her Türkçe cümle tek bir İngilizce cümle.** 1 saniyelik parça tek başına okununca hem anlatıcı hem
   çeviren model bozuyor ("Bottom line." gibi). Araç cümleyi nokta, soru ve ünlem işaretinden böler; bu yüzden ortaya
   iki nokta ya da noktalı virgül de, kısaltırken soru işareti de koyma: "Question mark? Only answer." iki bozuk parça
   çıktı, "A question mark means only answer." tek parça.
5. ✍ **Kesme işareti ve tırnak yok.** Anlatıcı motoru kabul etmiyor: "it's" değil "it is".
6. ✍ **İngilizce dışında sayıyı yazıyla yaz.** Anlatıcı rakam okumuyor; İngilizcede araç kendisi çeviriyor.
7. **Müzik konuşmanın altında kısılsın.** Asıl videoda müzik sen konuşurken kısılıyorsa dublajda da öyle olmalı; araç
   müziği videonun kendi sesinden ayırdığı için bu kendiliğinden olur.
8. **Her cümle aynı ses seviyesinde.** Dönüştürülen bazı cümleler 10 desibel kadar kısık çıkıyor; araç hepsini eşitler.
9. **Kendi İngilizceni okumak işe yaramadı.** İngilizce bir kayıt verince ses daha benzer çıkar diye düşündüm; olmadı.
   10–30 saniyelik temiz, normal konuşma kaydın yeter.
10. **Başka dilde de aynı yol.** İspanyolcada tek fark anlatıcı. Bir cümlenin ilk kelimesi hiç duyulmadı; cümleyi
    değiştirince düzeldi. Bilmediğin bir dilde sonucu başka bir yapay zekâya dinletip çevirt (ben Gemini'ye dinlettim).
11. **Bütün videoyu bir kerede okutmadan önce küçük dene.** Uzun bir okumada tek bir cümle bitmezse eski sürüm bütün işi
    durduruyordu; araç artık bitmeyen cümleyi tek başına yeniden dener, bitenleri tutar.
12. **Sesini doğrudan klonlayan modeller bugün bu yolu geçemedi.** 12 Kasım gecesi aynı 40 saniyelik Short'u 4 ücretsiz
    yolla ve ElevenLabs'le dublajladım: sesi videonun kendi Türkçesinden almak bazı kelimeleri yuttu; IndexTTS İngilizceyi
    garip bir aksanla okudu; Qwen3-TTS ölçüde en çok yaklaştı (ses benzerliği 0,92, ElevenLabs 0,93) ama kulakta bu aracı
    geçemedi; Chatterbox'ın çok dilli sürümü yavaş konuştu, 13 cümlenin 7'si yerine sığmadı. Tonlamada önde olan yalnız
    paralı servis. Bu araç aksanı yerli anlatıcıdan, sesi senden alıyor; senin tonlaman taşınmıyor.
