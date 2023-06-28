# Swapper-AI

• [Özellikler](#Özellikler) • [Kurulum](#Kurulum) • [Kullanım](#Kullanım)


Kullanımı kolay bir GUI ile eğitim gerektirmeden fotoğraf ve videolar için yüz değiştirme yazılımı.


### Özellikler

- Sade ve hızlı çalışan bir GUI
- Kaynak/hedef fotoğraf ve videolarda belirli yüzleri seçebilme özelliği
- GFPGAN destekli yüz geliştirme seçeneği
- Video kare hızında kayıpsız sonuçlar alma
- Video sesinde kayıpsız sonuçlar alma
- Çözünürlük kaybı olmadan sonuçlar alma


### Kurulum

> Windows için [Visual Studio](https://visualstudio.microsoft.com/tr/downloads/) indirip yüklemeniz gerekir. Kurulum sırasında en azından C++ paketini ve Python'u eklediğinizden emin olun.

Buna ek olarak, tek tıklamayla yükleyiciyi kullanmanız yeterlidir. Bu, her şeyi kullanışlı bir conda ortamında indirip yükleyecektir.

Diğer işletim sistemlerinde kullanmak isterseniz ya da kendiniz manuel kurulum yapmayı tercih ederseniz;

- `git clone https://github.com/CheddarSoftware/Swapper-AI`
- `pip install -r requirements.txt`

Video yüzünü değiştirmek için ayrıca ffmpeg'i düzgün bir şekilde kurmuş olmanız gerekir.


### Kullanım

- Windows: installer klasöründeki `windows_run.bat` dosyasını çalıştırın. İstediğiniz komut satırı bağımsız değişkenlerini eklemek için .bat dosyasını düzenleyin.
- Linux: `python run.py (ve isteğe bağlı komut satırı bağımsız değişkenleri)`

## Krediler

- [ffmpeg](https://ffmpeg.org/): Video ile ilgili işlemleri kolaylaştırmak için
- [deepinsight](https://github.com/deepinsight): kullanılan veri modeli için [insightface](https://github.com/deepinsight/insightface).
- Ömer Faruk Kızrak: Yazılımın geliştirilme sürecinde yüzünü ve bedenini bizler için feda ettiği için.
- Burak Can Bozlurt: Hiçbir sikim yapmadı ama sırf ona sövmek için burada yer veriyorum, amınakodumun kaşarlı su böreği.