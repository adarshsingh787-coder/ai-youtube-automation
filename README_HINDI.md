# AI YouTube Automation — हिंदी में आसान गाइड

यह प्रोजेक्ट रोज़ एक हिंदी हॉरर/सस्पेंस YouTube Short बनाने और YouTube पर अपलोड करने के लिए है। शुरुआती सुरक्षा के लिए अपलोड **Private** रखा गया है। पहले टेस्ट करें, फिर चाहें तो workflow में `VIDEO_PRIVACY: private` को `unlisted` या `public` बदलें।

## इसमें क्या-क्या होगा?
1. OpenAI से छोटी हिंदी हॉरर कहानी, शीर्षक और विवरण बनेंगे।
2. Replicate के `prunaai/p-video-2-pro` मॉडल से 9:16 वर्टिकल वीडियो बनेगा।
3. OpenAI text-to-speech से हिंदी narration बनेगी और वीडियो के साथ जोड़ी जाएगी।
4. YouTube Data API से वीडियो अपलोड होगा।
5. GitHub Actions रोज़ लगभग रात 9:07 बजे IST पर चलने के लिए सेट है; GitHub में देरी हो सकती है।

## पहले ये अकाउंट/चीज़ें चाहिए
- GitHub account
- OpenAI API key (API billing अलग हो सकती है)
- Replicate API token (वीडियो बनाने में शुल्क लग सकता है)
- YouTube channel और Google Cloud project में YouTube Data API v3 enabled

**महत्वपूर्ण:** ChatGPT subscription अपने-आप OpenAI API credit नहीं देता। OpenAI और Replicate दोनों की लागत हो सकती है। मॉडल की कीमत पहले जाँचें।

## चरण 1 — GitHub में repository बनाएँ
1. GitHub पर लॉगिन करें: https://github.com/new
2. Repository name लिखें: `ai-youtube-automation`
3. `Public` या `Private` चुनें; बेहतर है `Private`.
4. `Add a README file` को चुनें और **Create repository** दबाएँ.
5. ZIP को फोन/कंप्यूटर पर extract करके repository में फाइलें upload करें। GitHub में `Add file` → `Upload files` दबाएँ। पूरी फोल्डर संरचना सहित फाइलें upload करें, फिर `Commit changes` करें। `.github/workflows/daily-short.yml` भी ज़रूर अपलोड होनी चाहिए।

## चरण 2 — API keys GitHub Secrets में जोड़ें
Repository खोलें → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`.
नीचे दिए गए नाम ठीक वैसे ही डालें:

| Secret name | कहाँ से मिलेगा |
|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `REPLICATE_API_TOKEN` | https://replicate.com/account/api-tokens |
| `YOUTUBE_CLIENT_ID` | Google Cloud OAuth client |
| `YOUTUBE_CLIENT_SECRET` | उसी OAuth client में |
| `YOUTUBE_REFRESH_TOKEN` | चरण 3 के बाद मिलेगा |

इन keys को कभी README, source code या public chat में न लिखें।

## चरण 3 — YouTube OAuth सेट करें (एक बार)
यह सबसे तकनीकी चरण है और Google Cloud में अनुमति देना ज़रूरी है:
1. https://console.cloud.google.com/ खोलें और नया project बनाएँ।
2. `APIs & Services` → `Library` में `YouTube Data API v3` खोजकर Enable करें।
3. `Google Auth Platform` / `OAuth consent screen` में app configure करें। यदि app `Testing` में है, तो अपने YouTube channel वाले Google account को `Test user` में जोड़ें।
4. `Clients` में `Create client` चुनें और `Desktop app` बनाएँ। Client ID और Client secret को GitHub Secrets में डालें।
5. Desktop OAuth client की JSON फाइल डाउनलोड करें और उसका नाम `client_secret.json` रखें। इसे किसी के साथ share न करें।
6. अपने कंप्यूटर पर Python install करें, फिर इस repository की directory में terminal खोलकर चलाएँ:

```bash
pip install -r requirements.txt
python get_youtube_refresh_token.py
```

ब्राउज़र में Google अनुमति दें। स्क्रिप्ट एक refresh token दिखाएगी। उसे GitHub Secret `YOUTUBE_REFRESH_TOKEN` में डालें। Token को चैट या public repository में न डालें।

**यदि आपके पास केवल Android फोन है:** Google Cloud/OAuth का यह चरण फोन पर मुश्किल हो सकता है; कंप्यूटर पर एक बार करना आसान होगा। OAuth testing mode में refresh token की अवधि सीमित हो सकती है।

## चरण 4 — पहला टेस्ट
1. GitHub repository → `Actions` खोलें।
2. `Daily Hindi Horror Short` workflow चुनें।
3. `Run workflow` दबाएँ।
4. Run पर क्लिक करके logs देखें। सफल होने पर YouTube Studio में वीडियो `Private` दिखाई देगा।

## रोज़ का शेड्यूल
Workflow रोज़ `15:37 UTC` (भारत में लगभग `21:07`) पर चलता है। GitHub scheduled workflows में देरी संभव है। सार्वजनिक repositories में लंबे समय तक activity न होने पर schedule बंद भी हो सकता है।

## ज़रूरी नोट्स
- यह version रोज़ **एक 15-second के आसपास का Short** बनाने के लिए है, पूरा 60-second multi-scene edit नहीं।
- Replicate model schema/availability बदल सकती है। आधिकारिक schema देखें: https://replicate.com/prunaai/p-video-2-pro/api/schema
- API usage के हिसाब से खर्च होगा। पहले Private mode में एक manual test करें।
- Public करने से पहले वीडियो, आवाज़, title और copyright/YouTube policies की जाँच करें।
