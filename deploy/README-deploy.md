# Деплой портфолио на VM (nginx)

Сайт статический — поднимается за nginx без Django/Python на проде.

## 1. Подготовить файлы локально

Перед заливкой обнови список работ (если добавлял/менял файлы):

```
py gen_data.py
```

На прод нужны **все** файлы проекта, **кроме** dev-инструментов:
нужны `index.html`, `styles.css`, `script.js`, `data.js`, папка `posters/`
и папки с медиа (`Реклама/…`, `Спортивные Меропртия/…`).
`server.py`, `gen_data.py`, `deploy/` на прод копировать не обязательно.

## 2. Установить nginx на VM (Ubuntu/Debian)

```
sudo apt update && sudo apt install -y nginx
```

## 3. Скопировать сайт на VM

С локальной машины (пример через scp; запускать из папки проекта):

```
scp -r . user@IP_ВМ:/tmp/portfolio
```

На VM:

```
sudo mkdir -p /var/www/portfolio
sudo cp -r /tmp/portfolio/* /var/www/portfolio/
sudo chown -R www-data:www-data /var/www/portfolio
```

(Кириллические имена папок копируются нормально — кодировка UTF-8 уже учтена в конфиге.)

## 4. Подключить конфиг nginx

```
sudo cp /var/www/portfolio/deploy/nginx.conf /etc/nginx/sites-available/portfolio
# отредактируй server_name и root, если путь другой:
sudo nano /etc/nginx/sites-available/portfolio
sudo ln -s /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default   # убрать дефолтную заглушку
sudo nginx -t && sudo systemctl reload nginx
```

Открой `http://IP_ВМ` — сайт должен работать.

## 5. (опц.) Домен + HTTPS

Если есть домен, направь A-запись на IP VM и поставь бесплатный сертификат:

```
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d dmitryurusov.ru -d www.dmitryurusov.ru
```

## ⚠️ Важно про тяжёлые видео

Несколько роликов очень большие (`preview_RASA_v3.mp4` ~1 ГБ, `INTRO_…CSKA.mov` ~250 МБ,
`stardust_preview.mp4` ~100 МБ). На VM это:
- занимает место на диске,
- ест исходящий трафик при каждом просмотре.

Рекомендую перед заливкой пережать их в веб-формат (H.264, ~1080p, битрейт ~6–8 Мбит/с),
например через ffmpeg:

```
ffmpeg -i "вход.mp4" -vcodec libx264 -crf 23 -preset slow -vf "scale=-2:1080" -acodec aac -movflags +faststart "выход.mp4"
```

`-movflags +faststart` обязателен — позволяет видео начинать играть до полной загрузки.
`.mov` лучше сразу конвертировать в `.mp4` (Chrome/Firefox их не всегда играют).
После пережатия не забудь `py gen_data.py`, чтобы обновить размеры/список.
