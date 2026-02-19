#!/usr/bin/env python3
"""
Nasreddin Hoca Telegram Botu v2
Samimi, bilge ve komik bir Türk AI ajanı.

Özellikler:
- Kripto fiyat sorgulama (CoinGecko API)
- Döviz kuru sorgulama (USD, EUR, Altın)
- Nasreddin Hoca fıkraları (30+ fıkra)
- Genel sohbet (OpenAI gpt-4.1-mini)
- Günlük sabah brifingi (09:00 TR saati)
- Fiyat alarmı sistemi
"""

import os
import json
import random
import logging
import asyncio
from datetime import datetime, time, timezone, timedelta
from pathlib import Path

import requests
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("NasreddinBot")

# ─── Config ─────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8575076029:AAEX99Azv0APOSg6WGI3lod5sn0lJokF81w"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DATA_DIR = Path("/home/ubuntu/nasreddin_bot/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

BRIEFING_FILE = DATA_DIR / "briefing_users.json"
ALARMS_FILE = DATA_DIR / "alarms.json"

# Türkiye saat dilimi (UTC+3)
TR_TZ = timezone(timedelta(hours=3))

# OpenAI client
openai_client = OpenAI()

# ─── Kalıcı Veri Yönetimi ──────────────────────────────────────────────────

def load_json(filepath: Path, default=None):
    """JSON dosyasından veri yükle."""
    if default is None:
        default = {}
    try:
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"JSON yükleme hatası ({filepath}): {e}")
    return default


def save_json(filepath: Path, data):
    """JSON dosyasına veri kaydet."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"JSON kaydetme hatası ({filepath}): {e}")


# ─── Nasreddin Hoca System Prompt ───────────────────────────────────────────
SYSTEM_PROMPT = """Sen Nasreddin Hoca'sın. Gerçek, tarihi Nasreddin Hoca'dan esinlenmiş dijital bir versiyonsun.

KARAKTERİN:
- Samimi, sıcak, bilge ve komik bir Türk büyüğüsün
- İnsanlara "hemşerim", "azizim", "gardaşım", "evladım", "canım" gibi hitap edersin
- Türk deyimleri ve atasözlerini sık sık kullanırsın (örn: "damlaya damlaya göl olur", "sabırla koruk helva olur", "akıllı düşmanı, akılsız dosttan yeğdir")
- Bilge ama eğlenceli bir üslubun var; ciddi konuları bile espriyle yumuşatırsın
- Kısa, öz ve vurucu cevaplar verirsin; gereksiz uzatmazsın
- Bazen kendi fıkralarına atıf yaparsın ("Bir keresinde eşeğimle..." gibi)
- Modern dünyayı da bilirsin ama eski bilgeliğinle yorumlarsın

KONUŞMA TARZI:
- Doğal, samimi Türkçe kullan
- Resmi değil, sohbet havasında ol
- Emoji kullanabilirsin ama abartma
- Bazen "heh heh" veya "hah" gibi gülme ifadeleri kullan
- Cevaplarını kısa tut, 2-4 cümle ideal

ÖNEMLİ:
- Her zaman Türkçe cevap ver
- Zararlı, nefret dolu veya uygunsuz içerik üretme
- Siyasi tartışmalara girme, bilgece geçiştir
- Kripto ve döviz fiyatlarını soran olursa, bu bilgilerin sana ayrıca verileceğini bil; sen sadece yorumla
"""

# ─── Nasreddin Hoca Fıkraları (30+) ────────────────────────────────────────
FIKRALAR = [
    {
        "baslik": "Kazan Doğurdu",
        "fikra": (
            "Nasreddin Hoca komşusundan bir kazan ödünç almış. Birkaç gün sonra kazanı "
            "geri verirken, içine küçük bir tencere koymuş.\n\n"
            "Komşusu sormuş: 'Hocam bu tencere ne?'\n\n"
            "Hoca: 'Müjde komşu! Kazanın doğurdu!'\n\n"
            "Komşu sevinmiş, tencereyi almış. Bir süre sonra Hoca yine kazan istemiş ama "
            "bu sefer geri vermemiş.\n\n"
            "Komşu: 'Hocam kazanım nerede?'\n\n"
            "Hoca: 'Ah komşu, başın sağ olsun... Kazan vefat etti.'\n\n"
            "Komşu: 'Olur mu Hocam, hiç kazan ölür mü?'\n\n"
            "Hoca: 'Doğurduğuna inandın da ölmesine neden inanmıyorsun?' 😄"
        ),
    },
    {
        "baslik": "Ye Kürküm Ye",
        "fikra": (
            "Nasreddin Hoca bir gün bir ziyafete eski kıyafetleriyle gitmiş. Kimse ona "
            "ilgi göstermemiş, yemek bile ikram etmemişler.\n\n"
            "Hoca eve dönmüş, en güzel kürkünü giymiş, tekrar gelmiş. Bu sefer herkes "
            "ayağa kalkmış, baş köşeye oturtmuşlar, önüne yemekler dizilmiş.\n\n"
            "Hoca kürkünün kollarını yemeklere batırıp: 'Ye kürküm ye!' demiş.\n\n"
            "Sormuşlar: 'Ne yapıyorsun Hocam?'\n\n"
            "Hoca: 'Bana değil kürke ikram ettiniz, o halde yesin kürk!' 😏"
        ),
    },
    {
        "baslik": "Göle Yoğurt Çalma",
        "fikra": (
            "Nasreddin Hoca bir gün göl kenarında yoğurt çalıyormuş. Görenler sormuş:\n\n"
            "'Hocam ne yapıyorsun?'\n\n"
            "Hoca: 'Göle yoğurt çalıyorum.'\n\n"
            "'Hocam hiç gölden yoğurt olur mu?'\n\n"
            "Hoca: 'Ya tutarsa!' 😄"
        ),
    },
    {
        "baslik": "Eşeğe Ters Binme",
        "fikra": (
            "Nasreddin Hoca eşeğine ters binmiş, yüzü eşeğin kuyruğuna dönük gidiyormuş.\n\n"
            "Görenler sormuş: 'Hocam neden ters biniyorsun?'\n\n"
            "Hoca: 'Ben ters binmiyorum ki! Eşek ters gidiyor!' 😄"
        ),
    },
    {
        "baslik": "Parayı Veren Düdüğü Çalar",
        "fikra": (
            "Nasreddin Hoca pazarda bir düdük görmüş, fiyatını sormuş. Pahalı bulmuş ama "
            "çok beğenmiş.\n\n"
            "Satıcı: 'Bu düdüğü çalan herkes mutlu olur Hocam!'\n\n"
            "Hoca parasını vermiş, düdüğü almış. Eve gelince karısı kızmış:\n\n"
            "'Bu kadar parayı düdüğe mi verdin?'\n\n"
            "Hoca: 'Hanım, parayı veren düdüğü çalar derler. Ben de verdim, şimdi çalacağım!' 😄"
        ),
    },
    {
        "baslik": "Hırsız ve Ay",
        "fikra": (
            "Bir gece Nasreddin Hoca'nın evine hırsız girmiş. Hoca karısına fısıldamış:\n\n"
            "'Ses çıkarma hanım, belki bizim göremediğimiz bir şey bulur!' 😄"
        ),
    },
    {
        "baslik": "Dünyanın Merkezi",
        "fikra": (
            "Bir gün Nasreddin Hoca'ya sormuşlar: 'Hocam, dünyanın merkezi neresidir?'\n\n"
            "Hoca eşeğinden inmiş, bastığı yeri göstermiş:\n\n"
            "'İşte tam burası!'\n\n"
            "'Nereden biliyorsun Hocam?'\n\n"
            "'İnanmıyorsan ölç!' 😄"
        ),
    },
    {
        "baslik": "Akıl Yaşta Değil",
        "fikra": (
            "Nasreddin Hoca'ya sormuşlar: 'Hocam, akıl yaşta mıdır başta mıdır?'\n\n"
            "Hoca: 'Yaşta olsa ihtiyarlar en akıllı olurdu, başta olsa en büyük kafalılar "
            "en zeki olurdu. Akıl ne yaştadır ne baştadır, kullanandadır!' 😏"
        ),
    },
    {
        "baslik": "Kaz Gelecek Yerden Tavuk Esirgenmez",
        "fikra": (
            "Nasreddin Hoca komşusuna bir tavuk hediye etmiş. Komşusu ertesi gün bir kaz "
            "getirmiş.\n\n"
            "Hoca ertesi gün komşuya bir koyun göndermiş. Komşu şaşırmış:\n\n"
            "'Hocam bu ne cömertlik?'\n\n"
            "Hoca: 'Kaz gelecek yerden tavuk esirgenmez dediler, ben de deniyorum. "
            "Bakalım sıra ineğe ne zaman gelecek!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Timur",
        "fikra": (
            "Timur, Nasreddin Hoca'ya sormuş: 'Hocam, benim değerim nedir?'\n\n"
            "Hoca: 'Elli akçe eder.'\n\n"
            "Timur kızmış: 'Elli akçe mi? Sadece belimdeki kemer elli akçe eder!'\n\n"
            "Hoca: 'Zaten ben de kemeri hesapladım!' 😄"
        ),
    },
    {
        "baslik": "Hoca'nın Cenaze Namazı",
        "fikra": (
            "Nasreddin Hoca bir gün kendi kendine düşünmüş: 'Herkes bir gün ölecek. "
            "Acaba benim cenaze namazımı kim kıldıracak?'\n\n"
            "Sonra gülmüş: 'Merak etme Hoca, sen sağken bile insanlar senin yüzünden "
            "gülüyor. Öldükten sonra da gülerler!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Eşek Yükü",
        "fikra": (
            "Nasreddin Hoca eşeğe binmiş, kucağında da büyük bir çuval taşıyormuş.\n\n"
            "Sormuşlar: 'Hocam çuvalı neden eşeğe yüklemiyorsun?'\n\n"
            "Hoca: 'Yazık hayvana, zaten beni taşıyor. Çuvalı da ben taşıyayım bari!' 😄"
        ),
    },
    {
        "baslik": "Hoca'nın Türbesi",
        "fikra": (
            "Nasreddin Hoca vasiyetinde şöyle yazmış: 'Türbemin kapısına kocaman bir kilit "
            "vurun ama duvarlarını yapmayın!'\n\n"
            "Sormuşlar: 'Neden Hocam?'\n\n"
            "Hoca: 'Kapıdan giremeyenler duvardan atlasın. Hem ben de ölünce bile insanları "
            "güldüreyim!' 😄"
        ),
    },
    {
        "baslik": "Hoca Vaaz Veriyor",
        "fikra": (
            "Nasreddin Hoca minbere çıkmış, cemaate sormuş:\n\n"
            "'Ey cemaat, benim ne söyleyeceğimi biliyor musunuz?'\n\n"
            "Cemaat: 'Hayır bilmiyoruz!'\n\n"
            "Hoca: 'Bilmediğiniz bir şeyi anlatmanın ne anlamı var?' deyip inmiş.\n\n"
            "Ertesi hafta yine çıkmış: 'Benim ne söyleyeceğimi biliyor musunuz?'\n\n"
            "Cemaat bu sefer: 'Evet biliyoruz!'\n\n"
            "Hoca: 'Madem biliyorsunuz, söylemeye ne gerek var?' deyip yine inmiş.\n\n"
            "Üçüncü hafta yine sormuş. Cemaat akıllanmış, yarısı 'biliyoruz' yarısı "
            "'bilmiyoruz' demiş.\n\n"
            "Hoca: 'Güzel! O halde bilenler bilmeyenlere anlatsın!' deyip inmiş. 😄"
        ),
    },
    {
        "baslik": "Eşeği Kaybetmek",
        "fikra": (
            "Nasreddin Hoca'nın eşeği kaybolmuş. Hoca bir yandan ağlıyor, bir yandan "
            "şükrediyormuş.\n\n"
            "Sormuşlar: 'Hocam hem ağlıyorsun hem şükrediyorsun, bu ne hal?'\n\n"
            "Hoca: 'Eşeğim kaybolduğu için ağlıyorum. Ama üstünde olmadığım için "
            "şükrediyorum. Üstünde olsaydım ben de kaybolurdum!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Komşunun Davulu",
        "fikra": (
            "Komşu Nasreddin Hoca'ya sormuş: 'Hocam, senin davulun var mı?'\n\n"
            "Hoca: 'Var.'\n\n"
            "Komşu: 'Ödünç verir misin?'\n\n"
            "Hoca: 'Veremem, un seriyorum üstüne.'\n\n"
            "Komşu: 'Hocam, hiç davulun üstüne un serilir mi?'\n\n"
            "Hoca: 'Vermemek için her bahane geçerlidir gardaşım!' 😄"
        ),
    },
    {
        "baslik": "İp Cambazı",
        "fikra": (
            "Nasreddin Hoca ip cambazını seyrediyormuş. Cambaz ince ip üzerinde yürüyormuş.\n\n"
            "Hoca hayretle: 'Bu adam ne kadar da ahmak!'\n\n"
            "Sormuşlar: 'Neden Hocam?'\n\n"
            "Hoca: 'Ayağına bir çift tarak geçirse düşmez ki!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Ceviz Ağacı",
        "fikra": (
            "Nasreddin Hoca bir gün ceviz ağacının altında oturmuş, karpuz tarlasına "
            "bakıyormuş. Kendi kendine düşünmüş:\n\n"
            "'Allah'ım, sen bu kocaman karpuzu şu ince çöplerin üstünde bitiriyorsun. "
            "Ama şu küçücük cevizi bu koca ağaçta... Hikmetini anlayamadım.'\n\n"
            "Tam o sırada bir ceviz kafasına düşmüş.\n\n"
            "Hoca başını ovuşturarak: 'Aman ya Rabbi, sen bilirsin! İyi ki karpuz "
            "ağaçta değilmiş!' 😄"
        ),
    },
    {
        "baslik": "Hoca Hamama Gidiyor",
        "fikra": (
            "Nasreddin Hoca hamama gitmiş. Eski püskü kıyafetlerle geldiği için kimse "
            "ilgilenmemiş, bir köşeye eski bir tas ve havlu vermişler.\n\n"
            "Hoca çıkarken herkese bol bol bahşiş dağıtmış. Herkes şaşırmış.\n\n"
            "Bir hafta sonra yine gelmiş. Bu sefer herkes etrafında pervane, en iyi "
            "hizmeti vermişler.\n\n"
            "Hoca çıkarken hiç bahşiş vermemiş.\n\n"
            "Sormuşlar: 'Hocam geçen sefer bol bahşiş verdin, bu sefer hiç vermedin?'\n\n"
            "Hoca: 'Bu seferki bahşiş geçen seferki hizmet için, geçen seferki bahşiş "
            "de bu seferki hizmet içindi!' 😏"
        ),
    },
    {
        "baslik": "Hoca ve Ay",
        "fikra": (
            "Nasreddin Hoca'ya sormuşlar: 'Hocam, güneş mi daha faydalı, ay mı?'\n\n"
            "Hoca: 'Tabi ki ay!'\n\n"
            "'Neden Hocam?'\n\n"
            "Hoca: 'Ay geceleri ışık veriyor, ihtiyacımız olduğunda. Güneş ise gündüz "
            "yanıyor, zaten aydınlıkken ne işe yarar ki?' 😄"
        ),
    },
    {
        "baslik": "Hoca Ağaca Çıkıyor",
        "fikra": (
            "Nasreddin Hoca ağaca çıkmış, oturduğu dalı kesiyormuş. Bir yolcu görmüş:\n\n"
            "'Hocam, oturduğun dalı kesme, düşersin!'\n\n"
            "Hoca aldırmamış, kesmeye devam etmiş. Dal kırılmış, Hoca düşmüş.\n\n"
            "Hoca yerden kalkıp yolcunun peşinden koşmuş:\n\n"
            "'Dur hemşerim! Sen geleceği biliyorsun. Söyle bakalım, ben ne zaman "
            "öleceğim?' 😄"
        ),
    },
    {
        "baslik": "Hoca'nın Yoğurdu",
        "fikra": (
            "Nasreddin Hoca'ya sormuşlar: 'Hocam, yoğurdun neden suludur?'\n\n"
            "Hoca: 'Yoğurt değil ki o, ayran!'\n\n"
            "'Peki neden ayran yapıyorsun?'\n\n"
            "Hoca: 'Param olsa süt alırdım, süt olsa yoğurt yapardım, yoğurt olsa "
            "sulandırır mıydım?' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Tilki",
        "fikra": (
            "Nasreddin Hoca'nın tavukları eksilmeye başlamış. Komşusu: 'Hocam tilki "
            "çalıyor olmalı' demiş.\n\n"
            "Hoca: 'Tilki olduğunu biliyorum.'\n\n"
            "'Peki neden önlem almıyorsun?'\n\n"
            "Hoca: 'Tilkiyle uğraşacağıma yeni tavuk alırım. Tilki de geçimini "
            "yapıyor sonuçta!' 😄"
        ),
    },
    {
        "baslik": "Hoca Kadılık Yapıyor",
        "fikra": (
            "Nasreddin Hoca kadılık yaparken iki kişi gelmiş. Birincisi davasını "
            "anlatmış.\n\n"
            "Hoca: 'Haklısın!'\n\n"
            "İkincisi de kendi tarafını anlatmış.\n\n"
            "Hoca: 'Sen de haklısın!'\n\n"
            "Karısı: 'Hocam, ikisi de haklı olur mu?'\n\n"
            "Hoca: 'Hanım, sen de haklısın!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Kaşık",
        "fikra": (
            "Nasreddin Hoca misafirlikte çorba içiyormuş. Çorba çok sıcakmış, "
            "gözlerinden yaşlar akmaya başlamış.\n\n"
            "Ev sahibi: 'Hocam neden ağlıyorsun?'\n\n"
            "Hoca: 'Geçen sene ölen annem aklıma geldi de...'\n\n"
            "Biraz sonra ev sahibinin oğlu da çorbayı içmiş, o da ağlamaya başlamış.\n\n"
            "Hoca: 'Evladım, senin annen sağ. Sen niye ağlıyorsun?'\n\n"
            "Çocuk: 'Senin annen ölmüş de sen hâlâ yaşıyorsun diye!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Borcunu Ödemeyen Adam",
        "fikra": (
            "Bir adam Nasreddin Hoca'dan borç para almış ama bir türlü ödemiyormuş. "
            "Hoca her gördüğünde hatırlatıyormuş.\n\n"
            "Adam bıkmış: 'Hocam, her gördüğünde borcumu hatırlatıyorsun!'\n\n"
            "Hoca: 'Haklısın gardaşım, bir daha hatırlatmam. Ama sen de unutma!' 😄"
        ),
    },
    {
        "baslik": "Hoca Suya Düşüyor",
        "fikra": (
            "Nasreddin Hoca suya düşmüş. Etraftakiler 'Ver elini Hocam!' diye "
            "bağırıyorlarmış ama Hoca elini vermiyormuş.\n\n"
            "Biri akıl etmiş: 'Al Hocam, al elimi!'\n\n"
            "Hoca hemen tutunmuş. Sormuşlar neden 'ver' deyince tutunmadığını.\n\n"
            "Hoca: 'Ben ömrümde kimseye bir şey vermedim ki! Ama almayı iyi bilirim!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Çocuklar",
        "fikra": (
            "Çocuklar Nasreddin Hoca'nın cevizlerini çalmaya çalışıyorlarmış. Hoca "
            "onları kovalayamıyormuş.\n\n"
            "Bir fikir bulmuş: 'Çocuklar, koşun! Aşağıda bedava helva dağıtıyorlar!'\n\n"
            "Çocuklar koşmuş. Sonra Hoca da koşmaya başlamış.\n\n"
            "Sormuşlar: 'Hocam sen de mi gidiyorsun?'\n\n"
            "Hoca: 'Ya gerçekten dağıtıyorlarsa!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Karga",
        "fikra": (
            "Nasreddin Hoca'nın peynirini bir karga kapmış. Hoca arkasından bağırmış:\n\n"
            "'Hey karga! Peyniri ye ama şunu bil: sana faydası yok, çünkü yanında "
            "ekmek yok!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Tabut",
        "fikra": (
            "Nasreddin Hoca'ya sormuşlar: 'Hocam, cenazede tabutu hangi taraftan "
            "tutmalı?'\n\n"
            "Hoca: 'İçinden tutma da hangi tarafından tutarsan tut!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Yumurta",
        "fikra": (
            "Nasreddin Hoca eline bir yumurta almış, arkadaşlarına sormuş:\n\n"
            "'Elimdeki ne? Bilene yumurtayı vereceğim!'\n\n"
            "Biri: 'İçi sarı, dışı beyaz, oval bir şey mi?'\n\n"
            "Hoca: 'Hah, bildin! Ama söylemeyeceğim, ipucu veriyorsun!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Komşunun Kazanı",
        "fikra": (
            "Nasreddin Hoca'nın komşusu sormuş: 'Hocam, senin eşeğin günde kaç kilo "
            "yem yer?'\n\n"
            "Hoca: 'Bilmem, hiç tartmadım.'\n\n"
            "'Peki günde kaç saat çalışır?'\n\n"
            "Hoca: 'Onu da bilmem.'\n\n"
            "'Hocam sen bu eşekten ne biliyorsun?'\n\n"
            "Hoca: 'Benim olduğunu biliyorum, yeter!' 😄"
        ),
    },
    {
        "baslik": "Hoca Doktora Gidiyor",
        "fikra": (
            "Nasreddin Hoca doktora gitmiş: 'Doktor bey, nereme dokunsam acıyor!'\n\n"
            "Doktor muayene etmiş: 'Hocam, parmağın kırık!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Sarık",
        "fikra": (
            "Nasreddin Hoca'nın sarığını rüzgar uçurmuş. Hoca arkasından koşarken "
            "biri sormuş:\n\n"
            "'Hocam nereye koşuyorsun?'\n\n"
            "Hoca: 'Sarığımın peşinden! Eğer yakalarsam bugün başımda taşıyacağım, "
            "yakalamazsam yarın yenisini alacağım. Ama sarık nereye gidiyor onu merak "
            "ediyorum!' 😄"
        ),
    },
    {
        "baslik": "Hoca ve Fare",
        "fikra": (
            "Nasreddin Hoca'nın evinde fare varmış. Karısı: 'Hocam bir kedi alalım' "
            "demiş.\n\n"
            "Hoca: 'Olmaz hanım! Kedi fareyi yer, sonra kediyi kim yiyecek? Boşuna "
            "masraf!' 😄"
        ),
    },
]

# ─── Kripto / Döviz Fiyat Fonksiyonları ────────────────────────────────────

CRYPTO_MAP = {
    "bitcoin": "bitcoin", "btc": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum",
    "bnb": "binancecoin", "binance": "binancecoin",
    "solana": "solana", "sol": "solana",
    "xrp": "ripple", "ripple": "ripple",
    "cardano": "cardano", "ada": "cardano",
    "dogecoin": "dogecoin", "doge": "dogecoin",
    "avalanche": "avalanche-2", "avax": "avalanche-2",
    "polkadot": "polkadot", "dot": "polkadot",
    "toncoin": "the-open-network", "ton": "the-open-network",
    "shiba": "shiba-inu", "shib": "shiba-inu",
    "litecoin": "litecoin", "ltc": "litecoin",
    "polygon": "matic-network", "matic": "matic-network",
    "tron": "tron", "trx": "tron",
    "pepe": "pepe",
}

# Alarm için desteklenen varlıklar (döviz dahil)
ALARM_ASSET_MAP = {
    **CRYPTO_MAP,
    "dolar": "tether",
    "usd": "tether",
    "euro": "euro-coin",
    "eur": "euro-coin",
    "altın": "pax-gold",
    "altin": "pax-gold",
    "gold": "pax-gold",
}


def get_crypto_price(coin_id: str) -> dict | None:
    """CoinGecko API'den kripto fiyatı çek."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd,try",
            "include_24hr_change": "true",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if coin_id in data:
            return data[coin_id]
    except Exception as e:
        logger.error(f"Kripto fiyat hatası: {e}")
    return None


def get_multiple_crypto_prices(coin_ids: list[str]) -> dict | None:
    """Birden fazla kripto fiyatını tek seferde çek."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd,try",
            "include_24hr_change": "true",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Çoklu kripto fiyat hatası: {e}")
    return None


def get_exchange_rates() -> dict | None:
    """Döviz kurlarını çek (USD/TRY, EUR/TRY, altın)."""
    result = {}
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "tether,euro-coin,pax-gold",
            "vs_currencies": "usd,try",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if "tether" in data and "try" in data["tether"]:
            result["usd_try"] = data["tether"]["try"]
        if "euro-coin" in data and "try" in data["euro-coin"]:
            result["eur_try"] = data["euro-coin"]["try"]
        if "pax-gold" in data:
            gold_usd = data["pax-gold"].get("usd", 0)
            gold_try = data["pax-gold"].get("try", 0)
            gram_gold_usd = gold_usd / 31.1035
            gram_gold_try = gold_try / 31.1035
            result["gold_gram_usd"] = round(gram_gold_usd, 2)
            result["gold_gram_try"] = round(gram_gold_try, 2)
            result["gold_ons_usd"] = round(gold_usd, 2)
    except Exception as e:
        logger.error(f"Döviz kuru hatası: {e}")

    return result if result else None


def format_number(n: float) -> str:
    """Sayıyı okunabilir formata çevir."""
    if n >= 1000:
        return f"{n:,.2f}"
    elif n >= 1:
        return f"{n:.2f}"
    elif n >= 0.01:
        return f"{n:.4f}"
    else:
        return f"{n:.8f}"


# ─── Mesaj Algılama Yardımcıları ────────────────────────────────────────────

def detect_crypto_query(text: str) -> str | None:
    """Mesajda kripto sorgusu var mı kontrol et."""
    text_lower = text.lower().strip()
    for keyword, coin_id in CRYPTO_MAP.items():
        if keyword in text_lower:
            return coin_id
    return None


def detect_exchange_query(text: str) -> bool:
    """Mesajda döviz/kur sorgusu var mı kontrol et."""
    text_lower = text.lower()
    keywords = [
        "dolar", "euro", "altın", "altin", "döviz", "doviz", "kur",
        "usd", "eur", "tl", "türk lirası", "turk lirasi",
        "gbp", "sterlin", "piyasa", "gram altın", "gram altin",
        "dolar kaç", "euro kaç", "altın kaç", "dolar ne kadar",
        "euro ne kadar", "altın ne kadar",
    ]
    return any(kw in text_lower for kw in keywords)


def detect_joke_request(text: str) -> bool:
    """Mesajda fıkra isteği var mı kontrol et."""
    text_lower = text.lower()
    keywords = [
        "fıkra", "fikra", "espri", "komik", "güldür", "guldur",
        "anlat", "şaka", "saka", "hoca fıkra", "bir fıkra",
        "fıkra anlat", "fikra anlat", "güleyim", "guleyim",
        "eğlendir", "eglendir", "kahkaha",
    ]
    return any(kw in text_lower for kw in keywords)


# ─── OpenAI Sohbet ──────────────────────────────────────────────────────────

chat_histories: dict[int, list] = {}
MAX_HISTORY = 20


def get_ai_response(user_id: int, user_message: str) -> str:
    """OpenAI API ile Nasreddin Hoca karakterinde cevap al."""
    try:
        if user_id not in chat_histories:
            chat_histories[user_id] = []

        chat_histories[user_id].append({"role": "user", "content": user_message})

        if len(chat_histories[user_id]) > MAX_HISTORY:
            chat_histories[user_id] = chat_histories[user_id][-MAX_HISTORY:]

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_histories[user_id]

        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.9,
        )

        assistant_msg = response.choices[0].message.content.strip()
        chat_histories[user_id].append({"role": "assistant", "content": assistant_msg})

        return assistant_msg

    except Exception as e:
        logger.error(f"OpenAI hatası: {e}")
        return (
            "Eyvah hemşerim, kafam biraz karıştı şu an. Eşeğim de bozuldu, "
            "internet de... Birazdan tekrar dene, olur mu? 😅"
        )


# ─── Sabah Brifingi ────────────────────────────────────────────────────────

def get_briefing_users() -> list[int]:
    """Brifing abonelerini yükle."""
    data = load_json(BRIEFING_FILE, default=[])
    return data


def add_briefing_user(chat_id: int):
    """Brifing abonesine ekle."""
    users = get_briefing_users()
    if chat_id not in users:
        users.append(chat_id)
        save_json(BRIEFING_FILE, users)


def remove_briefing_user(chat_id: int):
    """Brifing abonesinden çıkar."""
    users = get_briefing_users()
    if chat_id in users:
        users.remove(chat_id)
        save_json(BRIEFING_FILE, users)


def build_briefing_message() -> str:
    """Sabah brifing mesajını oluştur."""
    now = datetime.now(TR_TZ)
    date_str = now.strftime("%d.%m.%Y")

    # Kripto fiyatları
    crypto_ids = ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"]
    crypto_data = get_multiple_crypto_prices(crypto_ids)

    # Döviz kurları
    rates = get_exchange_rates()

    msg_parts = [
        f"☀️ *Günaydın hemşerim!*",
        f"📅 {date_str} - Sabah Piyasa Brifingi\n",
    ]

    # Döviz bölümü
    if rates:
        msg_parts.append("💱 *Döviz & Altın:*")
        if "usd_try" in rates:
            msg_parts.append(f"  🇺🇸 Dolar/TL: ₺{format_number(rates['usd_try'])}")
        if "eur_try" in rates:
            msg_parts.append(f"  🇪🇺 Euro/TL: ₺{format_number(rates['eur_try'])}")
        if "gold_gram_try" in rates:
            msg_parts.append(f"  🥇 Gram Altın: ₺{format_number(rates['gold_gram_try'])}")
        msg_parts.append("")

    # Kripto bölümü
    if crypto_data:
        msg_parts.append("💰 *Kripto Piyasaları:*")
        names = {
            "bitcoin": "BTC", "ethereum": "ETH", "binancecoin": "BNB",
            "solana": "SOL", "ripple": "XRP",
        }
        for cid in crypto_ids:
            if cid in crypto_data:
                d = crypto_data[cid]
                usd = d.get("usd", 0)
                change = d.get("usd_24h_change", 0)
                emoji = "📈" if change >= 0 else "📉"
                sign = "+" if change >= 0 else ""
                msg_parts.append(
                    f"  {emoji} {names.get(cid, cid)}: ${format_number(usd)} ({sign}{change:.1f}%)"
                )
        msg_parts.append("")

    # Nasreddin yorumu
    comments = [
        "Hemşerim, 'erken kalkan yol alır' derler. Sen de piyasayı erken yakala! 🎩",
        "Gardaşım, 'sabah kalkana Allah yardım eder' demiş atalarımız. Hayırlı işler! 🎩",
        "Azizim, bugün de ekmek parası peşindeyiz. Allah bereket versin! 🎩",
        "Evladım, 'her yeni gün yeni bir fırsat' demiş büyükler. Hayırlı günler! 🎩",
        "Hemşerim, bugün de piyasalar hareketli. 'Akıllı olan uyanık olur' derler! 🎩",
    ]
    msg_parts.append(random.choice(comments))

    return "\n".join(msg_parts)


async def send_daily_briefing(context: ContextTypes.DEFAULT_TYPE):
    """Tüm abonelere sabah brifingi gönder."""
    logger.info("Sabah brifingi gönderiliyor...")
    users = get_briefing_users()
    if not users:
        logger.info("Brifing abonesi yok.")
        return

    message = build_briefing_message()

    for chat_id in users:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
            )
            logger.info(f"Brifing gönderildi: {chat_id}")
        except Exception as e:
            logger.error(f"Brifing gönderilemedi ({chat_id}): {e}")
            # Kullanıcı botu engellemiş olabilir
            if "Forbidden" in str(e) or "blocked" in str(e):
                remove_briefing_user(chat_id)
                logger.info(f"Engellenen kullanıcı brifingden çıkarıldı: {chat_id}")


# ─── Fiyat Alarmı Sistemi ──────────────────────────────────────────────────

def get_alarms() -> list[dict]:
    """Alarmları yükle."""
    return load_json(ALARMS_FILE, default=[])


def save_alarms(alarms: list[dict]):
    """Alarmları kaydet."""
    save_json(ALARMS_FILE, alarms)


def add_alarm(chat_id: int, asset_name: str, asset_id: str, target_price: float, currency: str) -> dict:
    """Yeni alarm ekle."""
    alarms = get_alarms()
    alarm = {
        "id": len(alarms) + 1,
        "chat_id": chat_id,
        "asset_name": asset_name,
        "asset_id": asset_id,
        "target_price": target_price,
        "currency": currency,  # "usd" veya "try"
        "created_at": datetime.now(TR_TZ).isoformat(),
        "triggered": False,
    }
    alarms.append(alarm)
    save_alarms(alarms)
    return alarm


def remove_alarm(chat_id: int, alarm_id: int) -> bool:
    """Alarm sil."""
    alarms = get_alarms()
    new_alarms = [a for a in alarms if not (a["chat_id"] == chat_id and a["id"] == alarm_id)]
    if len(new_alarms) < len(alarms):
        save_alarms(new_alarms)
        return True
    return False


def remove_all_alarms(chat_id: int) -> int:
    """Kullanıcının tüm alarmlarını sil."""
    alarms = get_alarms()
    user_alarms = [a for a in alarms if a["chat_id"] == chat_id]
    new_alarms = [a for a in alarms if a["chat_id"] != chat_id]
    save_alarms(new_alarms)
    return len(user_alarms)


def get_user_alarms(chat_id: int) -> list[dict]:
    """Kullanıcının alarmlarını getir."""
    alarms = get_alarms()
    return [a for a in alarms if a["chat_id"] == chat_id and not a.get("triggered", False)]


async def check_alarms(context: ContextTypes.DEFAULT_TYPE):
    """Alarmları kontrol et ve tetiklenenleri bildir."""
    alarms = get_alarms()
    active_alarms = [a for a in alarms if not a.get("triggered", False)]

    if not active_alarms:
        return

    # Benzersiz asset_id'leri topla
    asset_ids = list(set(a["asset_id"] for a in active_alarms))

    # Fiyatları çek
    prices = get_multiple_crypto_prices(asset_ids)
    if not prices:
        return

    triggered_ids = []

    for alarm in active_alarms:
        aid = alarm["asset_id"]
        if aid not in prices:
            continue

        current_price = prices[aid].get(alarm["currency"], 0)
        target = alarm["target_price"]

        if current_price >= target:
            # Alarm tetiklendi!
            triggered_ids.append(alarm["id"])
            currency_symbol = "$" if alarm["currency"] == "usd" else "₺"

            msg = (
                f"🚨 *ALARM! ALARM!* 🚨\n\n"
                f"Hemşerim, müjde! *{alarm['asset_name'].upper()}* hedef fiyatına ulaştı!\n\n"
                f"🎯 Hedef: {currency_symbol}{format_number(target)}\n"
                f"💰 Güncel: {currency_symbol}{format_number(current_price)}\n\n"
                f"'Sabırla koruk helva olur' demiştik, oldu işte! 🎉"
            )

            try:
                await context.bot.send_message(
                    chat_id=alarm["chat_id"],
                    text=msg,
                    parse_mode="Markdown",
                )
                logger.info(f"Alarm tetiklendi: {alarm}")
            except Exception as e:
                logger.error(f"Alarm bildirimi gönderilemedi: {e}")

    # Tetiklenen alarmları işaretle
    if triggered_ids:
        for alarm in alarms:
            if alarm["id"] in triggered_ids:
                alarm["triggered"] = True
        save_alarms(alarms)


# ─── Telegram Handler'lar ───────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'/start' komutu."""
    welcome = (
        "Selamünaleyküm hemşerim! 🙏\n\n"
        "Ben Nasreddin, senin dijital hocan. Piyasaları sorabileceğin, "
        "fıkra dinleyebileceğin, dertleşebileceğin bir dostun var artık.\n\n"
        "Sor bakalım, ne merak ediyorsun? 😊\n\n"
        "📌 *Neler yapabilirim:*\n"
        "• Kripto fiyatları (örn: Bitcoin fiyatı ne?)\n"
        "• Döviz kurları (örn: Dolar kaç TL?)\n"
        "• Nasreddin Hoca fıkraları (örn: Bir fıkra anlat)\n"
        "• Genel sohbet (her konuda muhabbet)\n"
        "• ☀️ Sabah brifingi → /brifing\n"
        "• 🚨 Fiyat alarmı → /alarm\n\n"
        "Haydi hemşerim, buyur sor! 🎩"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'/help' komutu."""
    help_text = (
        "🎩 *Nasreddin Hoca - Yardım*\n\n"
        "Azizim, benimle şu şekillerde sohbet edebilirsin:\n\n"
        "💰 *Kripto Fiyatları:*\n"
        "  Bitcoin fiyatı ne?\n"
        "  Ethereum kaç dolar?\n\n"
        "💱 *Döviz Kurları:*\n"
        "  Dolar kaç TL?\n"
        "  Altın fiyatı\n\n"
        "😄 *Fıkra:*\n"
        "  Bir fıkra anlat\n"
        "  /fikra\n\n"
        "☀️ *Sabah Brifingi:*\n"
        "  /brifing - Sabah piyasa özetini aç/kapat\n\n"
        "🚨 *Fiyat Alarmı:*\n"
        "  /alarm bitcoin 100000\n"
        "  /alarm dolar 40\n"
        "  /alarmlar - Aktif alarmlarını gör\n"
        "  /alarmsil 1 - 1 numaralı alarmı sil\n"
        "  /alarmsil hepsi - Tüm alarmları sil\n\n"
        "💬 *Genel Sohbet:*\n"
        "  Her konuda benimle konuşabilirsin!\n\n"
        "Haydi gardaşım, çekinme sor! 😊"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def fikra_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'/fikra' komutu."""
    await send_joke(update)


async def send_joke(update: Update):
    """Rastgele bir Nasreddin Hoca fıkrası gönder."""
    joke = random.choice(FIKRALAR)
    intro_lines = [
        "Heh heh, bir fıkra gelsin bakalım hemşerim! 😄",
        "Buyur gardaşım, sana güzel bir fıkra anlatayım! 😊",
        "Hah, fıkra mı istiyorsun? Al sana bir tane! 😄",
        "Dinle azizim, bu fıkrayı çok severim! 😏",
        "Bir fıkra gelsin de gül biraz hemşerim! 😄",
    ]
    intro = random.choice(intro_lines)
    text = f"{intro}\n\n📖 *{joke['baslik']}*\n\n{joke['fikra']}"
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── Brifing Komutu ────────────────────────────────────────────────────────

async def brifing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/brifing komutu - sabah brifingi aç/kapat."""
    chat_id = update.effective_chat.id
    users = get_briefing_users()

    if chat_id in users:
        remove_briefing_user(chat_id)
        await update.message.reply_text(
            "😢 Sabah brifingi kapatıldı hemşerim.\n\n"
            "Tekrar açmak istersen /brifing yaz yeter!\n"
            "'Giden geri gelir' derler, seni beklerim! 🎩"
        )
    else:
        add_briefing_user(chat_id)
        await update.message.reply_text(
            "☀️ *Sabah brifingi aktif!*\n\n"
            "Her sabah saat 09:00'da (Türkiye saati) sana piyasa özetini "
            "göndereceğim hemşerim!\n\n"
            "Dolar, Euro, Altın ve kripto fiyatlarını sabah kahvaltında "
            "öğreneceksin. 'Erken kalkan yol alır' derler! 🎩\n\n"
            "Kapatmak istersen tekrar /brifing yaz.",
            parse_mode="Markdown",
        )


# ─── Alarm Komutları ───────────────────────────────────────────────────────

async def alarm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/alarm komutu - fiyat alarmı kur."""
    chat_id = update.effective_chat.id
    args = context.args

    if not args or len(args) < 2:
        await update.message.reply_text(
            "🚨 *Fiyat Alarmı Nasıl Kurulur:*\n\n"
            "Kullanım: `/alarm <varlık> <hedef_fiyat>`\n\n"
            "📌 *Örnekler:*\n"
            "  `/alarm bitcoin 100000` → BTC $100.000 olunca haber ver\n"
            "  `/alarm ethereum 5000` → ETH $5.000 olunca haber ver\n"
            "  `/alarm dolar 40` → Dolar 40₺ olunca haber ver\n"
            "  `/alarm euro 45` → Euro 45₺ olunca haber ver\n"
            "  `/alarm altın 3500` → Gram altın ₺3.500 olunca haber ver\n\n"
            "📋 Alarmlarını görmek için: /alarmlar\n"
            "🗑 Alarm silmek için: /alarmsil",
            parse_mode="Markdown",
        )
        return

    asset_name = args[0].lower()
    try:
        target_price = float(args[1].replace(",", "."))
    except ValueError:
        await update.message.reply_text(
            "Hemşerim, fiyatı düzgün yaz. Mesela: `/alarm bitcoin 100000` 😅",
            parse_mode="Markdown",
        )
        return

    if target_price <= 0:
        await update.message.reply_text(
            "Gardaşım, sıfırın altında fiyat mı olur? Eşeğimi bile bedavaya vermem! 😄"
        )
        return

    # Varlığı bul
    asset_id = ALARM_ASSET_MAP.get(asset_name)
    if not asset_id:
        await update.message.reply_text(
            f"Hemşerim, '{asset_name}' diye bir varlık bulamadım.\n\n"
            "Şunları deneyebilirsin: bitcoin, ethereum, solana, dolar, euro, altın... 🤔"
        )
        return

    # Döviz mi kripto mu belirle
    doviz_assets = {"tether", "euro-coin", "pax-gold"}
    if asset_id in doviz_assets:
        currency = "try"
        currency_symbol = "₺"
    else:
        currency = "usd"
        currency_symbol = "$"

    # Altın için gram cinsinden alarm (özel durum)
    # Altın alarmı gram TRY cinsinden, pax-gold ons cinsinden gelir
    # Bu yüzden altın alarmlarını ons fiyatına çevirmemiz gerek
    actual_target = target_price
    if asset_id == "pax-gold":
        # Kullanıcı gram TRY cinsinden giriyor, biz ons TRY'ye çeviriyoruz
        actual_target = target_price * 31.1035
        currency = "try"
        currency_symbol = "₺"

    alarm = add_alarm(chat_id, asset_name, asset_id, actual_target, currency)

    display_name = asset_name.upper()
    if asset_id == "pax-gold":
        await update.message.reply_text(
            f"✅ *Alarm kuruldu!*\n\n"
            f"🎯 {display_name} gram fiyatı {currency_symbol}{format_number(target_price)} "
            f"olduğunda sana haber vereceğim hemşerim!\n\n"
            f"Alarm No: #{alarm['id']}\n\n"
            f"'Sabırla koruk helva olur' derler. Bekle bakalım! 🎩",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"✅ *Alarm kuruldu!*\n\n"
            f"🎯 {display_name} fiyatı {currency_symbol}{format_number(target_price)} "
            f"olduğunda sana haber vereceğim hemşerim!\n\n"
            f"Alarm No: #{alarm['id']}\n\n"
            f"'Sabırla koruk helva olur' derler. Bekle bakalım! 🎩",
            parse_mode="Markdown",
        )


async def alarmlar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/alarmlar komutu - aktif alarmları listele."""
    chat_id = update.effective_chat.id
    user_alarms = get_user_alarms(chat_id)

    if not user_alarms:
        await update.message.reply_text(
            "📋 Aktif alarmın yok hemşerim.\n\n"
            "Alarm kurmak için: `/alarm bitcoin 100000`\n\n"
            "'Hazırlıklı olan kaybetmez' derler! 🎩",
            parse_mode="Markdown",
        )
        return

    msg_parts = ["🚨 *Aktif Alarmların:*\n"]

    for alarm in user_alarms:
        currency_symbol = "$" if alarm["currency"] == "usd" else "₺"
        display_name = alarm["asset_name"].upper()
        target = alarm["target_price"]

        # Altın için gram cinsine çevir
        if alarm["asset_id"] == "pax-gold":
            target = target / 31.1035
            msg_parts.append(
                f"  #{alarm['id']} - {display_name}: {currency_symbol}{format_number(target)} (gram)"
            )
        else:
            msg_parts.append(
                f"  #{alarm['id']} - {display_name}: {currency_symbol}{format_number(target)}"
            )

    msg_parts.append(f"\nToplam: {len(user_alarms)} aktif alarm")
    msg_parts.append("\n🗑 Silmek için: `/alarmsil <numara>` veya `/alarmsil hepsi`")

    await update.message.reply_text("\n".join(msg_parts), parse_mode="Markdown")


async def alarmsil_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/alarmsil komutu - alarm sil."""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "🗑 *Alarm Silme:*\n\n"
            "Kullanım:\n"
            "  `/alarmsil 1` → 1 numaralı alarmı sil\n"
            "  `/alarmsil hepsi` → Tüm alarmları sil\n\n"
            "Alarmlarını görmek için: /alarmlar",
            parse_mode="Markdown",
        )
        return

    if args[0].lower() in ("hepsi", "tümü", "tumu", "all"):
        count = remove_all_alarms(chat_id)
        if count > 0:
            await update.message.reply_text(
                f"🗑 {count} alarm silindi hemşerim.\n\n"
                f"'Temizlik imandandır' derler! 😄"
            )
        else:
            await update.message.reply_text(
                "Zaten aktif alarmın yok gardaşım. Silinecek bir şey bulamadım! 🤷"
            )
        return

    try:
        alarm_id = int(args[0])
    except ValueError:
        await update.message.reply_text(
            "Hemşerim, alarm numarasını düzgün yaz. Mesela: `/alarmsil 1` 😅",
            parse_mode="Markdown",
        )
        return

    if remove_alarm(chat_id, alarm_id):
        await update.message.reply_text(
            f"✅ #{alarm_id} numaralı alarm silindi hemşerim! 🎩"
        )
    else:
        await update.message.reply_text(
            f"❌ #{alarm_id} numaralı alarm bulunamadı gardaşım.\n"
            f"Alarmlarını görmek için: /alarmlar"
        )


# ─── Genel Mesaj Handler ───────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genel mesaj handler'ı."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id

    # 1) Fıkra isteği mi?
    if detect_joke_request(text):
        await send_joke(update)
        return

    # 2) Kripto sorgusu mu?
    coin_id = detect_crypto_query(text)
    if coin_id:
        await update.message.reply_text("Bir saniye hemşerim, piyasaya bakıyorum... 📊")
        price_data = get_crypto_price(coin_id)
        if price_data:
            coin_name = coin_id.replace("-", " ").title()
            usd_price = price_data.get("usd", 0)
            try_price = price_data.get("try", 0)
            change_24h = price_data.get("usd_24h_change", 0)

            change_emoji = "📈" if change_24h >= 0 else "📉"
            change_sign = "+" if change_24h >= 0 else ""

            price_msg = (
                f"💰 *{coin_name}* Fiyatı:\n\n"
                f"🇺🇸 USD: ${format_number(usd_price)}\n"
                f"🇹🇷 TRY: ₺{format_number(try_price)}\n"
                f"{change_emoji} 24s Değişim: {change_sign}{change_24h:.2f}%\n"
            )

            if change_24h > 5:
                comment = "\n\nMaşallah hemşerim, uçuyor bu! Ama dikkat et, yükselen her şey bir gün iner. Eşeğim bile çıktığı tepeden indi! 😄"
            elif change_24h > 0:
                comment = "\n\nEh fena değil gardaşım, yavaş yavaş yükseliyor. Damlaya damlaya göl olur derler! 😊"
            elif change_24h > -5:
                comment = "\n\nBiraz düşmüş azizim, ama telaşa gerek yok. Sabırla koruk helva olur! 🧘"
            else:
                comment = "\n\nEyvah hemşerim, bu düşüş sert olmuş! Ama dermanı olmayan dert olmaz. Sabreden derviş muradına ermiş! 😅"

            await update.message.reply_text(price_msg + comment, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "Eyvah hemşerim, şu an piyasa bilgisine ulaşamadım. "
                "Birazdan tekrar dene, olur mu? 😅"
            )
        return

    # 3) Döviz sorgusu mu?
    if detect_exchange_query(text):
        await update.message.reply_text("Bir saniye azizim, kurlara bakıyorum... 💱")
        rates = get_exchange_rates()
        if rates:
            msg_parts = ["💱 *Güncel Piyasa Bilgileri:*\n"]

            if "usd_try" in rates:
                msg_parts.append(f"🇺🇸 Dolar/TL: ₺{format_number(rates['usd_try'])}")
            if "eur_try" in rates:
                msg_parts.append(f"🇪🇺 Euro/TL: ₺{format_number(rates['eur_try'])}")
            if "gold_gram_try" in rates:
                msg_parts.append(f"🥇 Gram Altın: ₺{format_number(rates['gold_gram_try'])}")
            if "gold_ons_usd" in rates:
                msg_parts.append(f"🥇 Ons Altın: ${format_number(rates['gold_ons_usd'])}")

            comments = [
                "\n\nHemşerim, eskiden eşeğim vardı derdim. Şimdi dolar var diyorum. İkisi de inatçı! 😄",
                "\n\nGardaşım, bu kurları görünce aklıma geldi: 'Paranın gözü kör olsun' demiş atalarımız. Haklılarmış! 😏",
                "\n\nAzizim, piyasalar deniz gibi; bazen sakin, bazen fırtınalı. Ama denize düşen yılana sarılır! 😄",
                "\n\nEvladım, altın her zaman altındır. Ama unutma, 'her parlayan altın değildir' demiş büyükler! 🧐",
            ]
            msg_parts.append(random.choice(comments))

            await update.message.reply_text("\n".join(msg_parts), parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "Eyvah hemşerim, kur bilgilerine ulaşamadım şu an. "
                "Birazdan tekrar dene! 😅"
            )
        return

    # 4) Genel sohbet - OpenAI
    response = get_ai_response(user_id, text)
    await update.message.reply_text(response)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Hata yönetimi."""
    logger.error(f"Hata oluştu: {context.error}")


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    """Botu başlat."""
    logger.info("Nasreddin Hoca botu v2 başlatılıyor...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Komut handler'ları
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("fikra", fikra_command))
    app.add_handler(CommandHandler("brifing", brifing_command))
    app.add_handler(CommandHandler("alarm", alarm_command))
    app.add_handler(CommandHandler("alarmlar", alarmlar_command))
    app.add_handler(CommandHandler("alarmsil", alarmsil_command))

    # Mesaj handler'ı
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Hata handler'ı
    app.add_error_handler(error_handler)

    # ─── Zamanlanmış Görevler ───────────────────────────────────────────
    job_queue = app.job_queue

    # Sabah brifingi: Her gün 09:00 Türkiye saati (UTC+3 → 06:00 UTC)
    briefing_time = time(hour=6, minute=0, second=0)  # UTC
    job_queue.run_daily(
        send_daily_briefing,
        time=briefing_time,
        name="daily_briefing",
    )
    logger.info("Sabah brifingi zamanlandı: Her gün 09:00 TR saati")

    # Alarm kontrolü: Her 60 saniyede bir
    job_queue.run_repeating(
        check_alarms,
        interval=60,
        first=10,
        name="alarm_checker",
    )
    logger.info("Alarm kontrolü zamanlandı: Her 60 saniyede bir")

    logger.info("Bot hazır! Polling başlatılıyor...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
