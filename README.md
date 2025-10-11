# WordPress Social Media Agent

Bu depo, WordPress siteniz **yenifikirler.org**'da yayınlanan yeni makaleleri X.com, LinkedIn, Facebook, Instagram, Pinterest ve TikTok gibi sosyal medya platformlarında otomatik olarak paylaşmak için tasarlanmış bir Python ajanı içerir. Ajan, WordPress RSS/Atom feed'ini izler, daha önce paylaşılmamış içerikleri tespit eder ve ilgili platform API'lerine gönderir.

## Özellikler

- WordPress feed'inden en yeni makaleleri toplar.
- Paylaşılmış gönderileri saklayarak tekrar paylaşımı engeller.
- X.com, LinkedIn, Facebook, Instagram, Pinterest ve TikTok için ayrı istemciler.
- `dry_run` modu ile gerçek paylaşımlar yapılmadan entegrasyonu test edebilirsiniz.
- Yapay zeka destekli görsel üretimi ile paylaşımlara eşlik eden özgün illüstrasyonlar oluşturur.
- YAML tabanlı yapılandırma ve `.env` dosyaları ile gizli anahtar yönetimi.

## Kurulum

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Yapılandırma

1. `agent.config.example.yaml` dosyasını `agent.config.yaml` adıyla kopyalayın ve değerleri güncelleyin (örnekteki varsayılan WordPress adresi yenifikirler.org olarak ayarlanmıştır).
2. Her platform için `enabled: true` olarak işaretleyin ve gerekli kimlik bilgilerini ekleyin.
3. `images` bölümünde yapay zeka sağlayıcısı kimlik bilgilerini (`api_key`, `model`, `prompt_template` vb.) doldurun; varsayılan ayarlar OpenAI `gpt-image-1` modeli ile çalışacak şekilde hazırlanmıştır.
4. Instagram ve Pinterest gibi platformlar bir görsel URL'si istediği için, sağlayıcınızın sunduğu barındırma bağlantısını (ör. OpenAI dönüşü) kullanın veya oluşturulan görselleri `output_dir` dizinine kaydedip dışarıdan erişilebilir bir alana yükleyin.
5. Gerekli API anahtarlarını `.env` dosyanıza yerleştirip `access_token` alanlarında `${ENV_VAR}` şeklinde kullanabilirsiniz. `dotenv` desteği ile bu değişkenler otomatik yüklenir.

```bash
cp agent.config.example.yaml agent.config.yaml
```

## Çalıştırma

Ajanı bir kez çalıştırarak sadece yeni makaleleri paylaşmak için:

```bash
social-agent run --config-path agent.config.yaml --once --verbose
```

Sürekli çalışacak bir servis olarak kullanmak için (ör. bir sistem servisine entegre ederek):

```bash
social-agent run --config-path agent.config.yaml --verbose
```

## Geliştirme

Kod Python 3.11+ sürümü ile test edilmiştir. Kod stilini kontrol etmek için:

```bash
python -m compileall social_agent
```

Testleri çalıştırmak için önce isteğe bağlı test bağımlılıklarını kurun ve ardından `pytest` çalıştırın:

```bash
pip install -e .[test]
pytest
```

## Güvenlik Notları

- API erişim anahtarlarını git deposuna eklemeyin.
- Yapay zeka görsel sağlayıcısı API anahtarlarınızı gizli tutun ve yalnızca çalışma ortamında kullanın.
- Instagram ve Pinterest için paylaşımlarda kullanılacak görsellerin herkese açık bir URL üzerinden erişilebilir olması gerekir; gerekiyorsa `generated_images/` dizinindeki çıktıları CDN veya WordPress ortam kitaplığına yükleyin.
- Gerçek gönderim öncesi `dry_run: true` ile yapılandırmayı doğrulayın.

## Lisans

Bu proje MIT lisansı altında sunulmaktadır.
