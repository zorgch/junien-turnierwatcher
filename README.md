# Deine ['ju:nien] Turnier-Mutter

Schickt Dir Telegram-Benachrichtigungen zu Turnierzeiten & deren Änderungen währen der LAN.

> So wie deine Mutti schaut dass Du immer pünktlich bist. Aber für ['ju:nien] Turniere:<br>
> Behält Deine angemeldeten Turniere im Blick, und gibt Dir Bescheid falls es Änderungen gab.<br>
> Denn wir wissen ja... die ['ju:nien] hat ihren eigenen Rhythmus.

> [!WARNING]
> Funktioniert natürlich nur so gut, wie die Zeiten vom Turnierbüro im Intranet Turniersystem ein- bzw. nachgetragen werden. Daher: keine Garantie! Heulen kannst daheim dann wieder.

## Was?

So schaut das dann ungefähr aus:

![Beispiel Telegram Nachrichten](/.github/howto-example-notifications.jpg)


## Wie?

### Das brauchts...

* Docker installiert
* Ein Telegram Bot Token<br>(bei [BotFather](https://telegram.me/BotFather) erstellen lassen, [Tutorial](https://core.telegram.org/bots/tutorial#introduction))
* (D)eine Telegram Chat ID (z.B. via [@userinfobot](https://telegram.me/userinfobot))
* Dein www.junien.net Intranet Cookie-Session Token

<details>
<summary>['ju:nien] Intranet Cookie-Token holen...</summary>

1. Geh an der LAN ins [Intranet](http://www.junien.net/)
2. Log dich mit einem User ein
3. Über die Web Dev Console, hol Dein `lk`-Cookie Wert (`value`)

![Junien Intranet "lk" Cookie rauskopieren](/.github/howto-lk-cookie-value.jpg)

</details>

> [!TIP]
> Trag alles in eine Kopie des `.env.example` ein!

### Starten

#### Mit Docker

1. `.env.example` kopiert und angepasst
2. Ins Verzeichnis der Turnier-Mutter navigieren

```bash
docker compose up -d
```

<br>

<details>
<summary>Ohne Docker (plain python)...</summary>

**Python dependencies installieren**

```bash
pip install requests beautifulsoup4
```

**Terminalbefehl**

*Linux / Mac*

```bash
env \
JUNIEN_INTRANET_LK_COOKIE_VALUE=M... \
JUNIEN_NUMMER=28 \
TELEGRAM_BOT_TOKEN=000000000:AAAAAAbbbbbbbCCCCCCCddddd-9zz8XX \
TELEGRAM_CHAT_ID=12345678 \
python turniermutter.py
```

*Windows (PowerShell)*

`$env:JUNIEN_NUMMER="28"; $env:JUNIEN_INTRANET_LK_COOKIE_VALUE="M..."; $env:TELEGRAM_BOT_TOKEN="000000000:AAAAAAbbbbbbbCCCCCCCddddd-9zz8XX"; $env:TELEGRAM_CHAT_ID="12345678"; python turniermutter.py`

</details>

## Attribution

Vibe Coded in zwei Stunden @ ['ju:nien] XXVIII - *28 Juniens later*, 25.10.2026, Hagen, Deutschland.
