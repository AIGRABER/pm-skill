<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**Yapay zeka destekli geliştirme için yerel öncelikli proje yönetimi.**

`pm-skill`, gereksinimleri, TODO kayıtlarını, dal ilerlemesini, kontrolleri, devir notlarını ve denetim izlerini Git deposunda tutar. Böylece insanlar ve coding agentlar, sohbet geçmişine değil depodaki gerçeklere bakarak devam edebilir.

## Neden var

AI kodlama oturumları güçlüdür, fakat proje durumu konuşmaların içinde dağılabilir. `pm-skill`, hangi dalda çalışıldığını, hangi TODOların bulunduğunu, hangi kontrollerin koştuğunu ve sıradaki adımı deponun açıklayabilmesini sağlar.

## Özellikler

- Yerel öncelikli: durum depoda saklanır.
- Dal farkındalığı: gereksinimler, TODOlar ve changeloglar dal bazında yönetilir.
- İnsan ve araçlar için okunabilir Markdown.
- CLI, REST ve MCP aynı command envelope kullanır.
- Yazma komutları `.pm-skill/audit/audit-log.jsonl` içine kaydedilir.

## Quick Start

```bash
pipx install git+https://github.com/AIGRABER/pm-skill.git
```

Kurulumdan sonra coding agent'a doğal dille ne istediğini söyle:

`pm-skill` sadece bağlam kurtarma aracı değildir. AI coding için depo içinde bir control plane sağlar: recover state -> discuss uncertainty -> extract draft requirements -> approve scope -> split TODOs -> constrain context -> verify acceptance -> audit changes -> handover/release.

```text
pm-skill ile C:\Users\win\Documents\MyProject projesini başlat. project id my-project, görünen ad "My Project" olsun.
```

```text
pm-skill ile proje control state'ini kurtar; mevcut dalı, değişmiş dosyaları, aktif gereksinimleri, açık TODOları, riskleri ve sonraki güvenli adımı söyle.
```

```text
Login yenilemesinin ne içermesi gerektiğinden emin değilim. Önce benimle tartış, netleştirici sorular sor, konuşmadan hedefleri, kısıtları, riskleri ve kabul kriterlerini çıkar, sonra pm-skill taslak gereksinimi olarak kaydet.
```

```text
"Login akışı ekle" işi için pm-skill çalışma yüzeyi oluştur ve deponun varsayılan kontrollerini çalıştır.
```

```text
"Şifresiz giriş" için pm-skill taslak gereksinimi oluştur; kodlamadan önce kapsam sınırı olarak hedefi, sahipleri, riskleri ve ilk kabul kriterlerini yaz.
```

```text
Magic-link sign-in kısmını resmi gereksinime yükselt, bu gereksinimden TODO oluştur ve kabul matrisi üret.
```

```text
İlk TODO için work package oluştur, agent'ın çalışma bağlamını sınırlamak için ilgili uygulama ve doğrulama dosyalarını ekle, bitirmeden önce kabul matrisini doğrula.
```

Başka bir dilde de istekte bulunabilirsin; agent doğal dili `pm-skill` komutlarına, REST'e veya MCP çağrılarına çevirir.

## Temel Fikirler

- Depodaki dosyalar doğruluk kaynağıdır.
- `.pm-skill/` makine tarafından okunabilir control-plane durumunu saklar.
- Markdown gereksinimleri, TODOları, changelogları, kabul notlarını ve handoverları saklar.
- CLI, REST ve MCP adaptörleri aynı command envelope kullanmalıdır.
- Yazma işlemleri denetlenir, böylece uzun AI coding işleri yeniden kurulabilir.

## Kullanışlı Komutlar

| Komut | Amaç |
| --- | --- |
| `pm-skill show-status --json` | Mevcut dalı, değişmiş dosyaları, aktif TODOları, uyarıları ve sonraki adımı gör. |
| `pm-skill recover-project --json` | Proje control state'ini ve bağlamı kurtar. |
| `pm-skill create-requirement --title "..." --json` | Konuşmadan veya açık bir tanımdan taslak gereksinim oluştur. |
| `pm-skill promote-requirement REQ-DRAFT-... --json` | Taslak gereksinimi resmi gereksinime yükselt. |
| `pm-skill create-todo-from-source --source-requirement REQ-... --json` | Resmi gereksinimden izlenebilir TODO oluştur. |
| `pm-skill create-acceptance-matrix TODO-... --json` | TODO için kabul matrisi üret. |
| `pm-skill create-work-package TODO-... --json` | Agent bağlamını sınırlayan focused work package oluştur. |
| `pm-skill validate-acceptance TODO-... --checks-profile default --json` | Kabul matrisi ve checks ile tamamlanma durumunu doğrula. |
| `pm-skill handover --summary-level standard --json` | Sonraki oturum için handover bırak. |

## License

Apache License 2.0. See [LICENSE](../../LICENSE).
