#!/usr/bin/env python3
"""
RG Display Server — local RS485 controller for R&G LED displays.
Run: python server.py [--port 8080] [--serial /dev/...]
"""
import argparse, json, math, os, serial, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from functools import partial

# ---- Clock Data (mirrors clock.hpp) ----
MONTH_PL = ["sty","lut","mar","kwi","maj","cze","lip","sie","wrz","paź","lis","gru"]
NAMEDAYS = [
    "Masław,Mieczysław,Mieczysława","Abel,Izydor,Makary","Arletta,Dan,Danisz",
    "Angelika,Aniela,Benedykta","Edward,Emilian,Emiliusz","Andrzej,Balcer,Baltazar",
    "Chociesław,Izydor,Julian","Erhard,Mścisław,Seweryn","Antoni,Bazylissa,Borzymir",
    "Agaton,Dobrosław,Jan","Feliks,Hilary,Honorata","Antoni,Arkadiusz,Arkady",
    "Bogumił,Bogusąd,Bogusława","Feliks,Hilary,Odo","Aleksander,Dąbrówka,Dobrawa",
    "Marcel,Waleriusz,Włodzimierz","Antoni,Jan,Rościsław","Bogumił,Jaropełk,Krystyna",
    "Andrzej,Bernard,Erwin","Dobiegniew,Fabian,Sebastian","Agnieszka,Epifani,Jarosław",
    "Anastazy,Dobromysł,Gaudencjusz","Emerencja,Ildefons,Jan","Chwalibóg,Felicja,Mirogniew",
    "Miłosz,Miłowan,Miłowit","Paula,Paulina,Polikarp","Angelika,Ilona,Jan Chryzostom",
    "Agnieszka,Augustyn,Flawian","Franciszek Salezy,Gilda,Hanna","Adelajda,Feliks,Gerard",
    "Cyrus,Euzebiusz,Jan","Bryda,Brygida,Dobrocha","Joanna,Korneliusz,Maria",
    "Błażej,Hipolit,Hipolita","Andrzej,Gilbert,Jan","Adelajda,Aga,Agata",
    "Angel,Angelus,Antoni","Romuald,Ryszard,Sulisław","Gniewomir,Gniewosz,Honorat",
    "Apolonia,Bernard,Cyryl","Elwira,Gabriel,Jacek","Adolf,Adolfa,Adolfina",
    "Aleksy,Benedykt,Eulalia","Benigna,Grzegorz,Jordan","Adolf,Adolfa,Adolfina",
    "Faustyn,Georgia,Georgina","Bernard,Dan,Danisz","Donat,Donata,Franciszek",
    "Albert,Alberta,Albertyna","Arnold,Arnolf,Bądzisława","Euchariusz,Eustachiusz,Eustachy",
    "Eleonora,Feliks,Fortunat","Małgorzata,Nikifor,Piotr","Bądzimir,Damian,Florentyn",
    "Bogurad,Bogusz,Boguta","Bolebor,Cezary,Konstancjusz","Aleksander,Bogumił,Cezariusz",
    "Aleksander,Anastazja,Auksencjusz","Chwalibóg,Józef,Makary","Albin,Antoni,Antonina",
    "Absalon,Franciszek,Halszka","Asteriusz,Hieronim,Kunegunda","Adrian,Adrianna,Arkadiusz",
    "Adrian,Adrianna,Fryderyk","Eugenia,Felicyta,Frydolin","Felicja,Nadmir,Paweł",
    "Beata,Filemon,Jan","Apollo,Dominik,Franciszka","Aleksander,Bożysław,Cyprian",
    "Benedykt,Drogosława,Edwin","Bernard,Blizbor,Grzegorz","Bożena,Ernest,Ernestyn",
    "Bożeciecha,Jakub,Leon","Gościmir,Heloiza,Klemens","Abraham,Cyriak,Henryka",
    "Gertruda,Harasym,Jan","Aleksander,Anzelm,Boguchwał","Bogdan,Józef",
    "Aleksander,Aleksandra,Ambroży","Benedykt,Filemon,Lubomira","Bazylissa,Bogusław,Godzisław",
    "Eberhard,Feliks,Katarzyna","Dziersława,Dzierżysława,Gabor","Dyzma,Ireneusz,Łucja",
    "Emanuel,Feliks,Larysa","Benedykt,Ernest,Ernestyn","Aniela,Antoni,Jan",
    "Cyryl,Czcirad,Eustachiusz","Amelia,Aniela,Częstobor","Amos,Balbina,Beniamin",
    "Chryzant,Grażyna,Hugo","Franciszek,Sądomir,Urban","Antoni,Cieszygor,Jakub",
    "Ambroży,Bazyli,Benedykt","Borzywoj,Irena,Wincenty","Ada,Adam,Adamina",
    "Donat,Donata,Epifaniusz","Apolinary,Cezary,Cezaryna","Dobrosława,Dymitr,Maja",
    "Antoni,Apoloniusz,Daniel","Filip,Herman,Jaromir","Andrzej,Iwan,Juliusz",
    "Hermenegild,Hermenegilda,Ida","Berenike,Julianna,Justyn","Anastazja,Bazyli,Leonid",
    "Benedykt,Bernadetta,Cecyl","Anicet,Innocenta,Innocenty","Apoloniusz,Bogusław,Bogusława",
    "Adolf,Adolfa,Adolfina","Agnieszka,Amalia,Czech","Addar,Anzelm,Bartosz",
    "Heliodor,Kajus,Leonia","Adalbert,Gerard,Gerarda","Aleksander,Aleksy,Egbert",
    "Jarosław,Marek,Wasyl","Artemon,Klaudiusz,Klet","Anastazy,Andrzej,Bożebor",
    "Arystarch,Maria,Paweł","Angelina,Augustyn,Bogusław","Bartłomiej,Chwalisława,Eutropiusz",
    "Aniela,Filip,Jakub","Afanazy,Anatol,Atanazy","Aleksander,Antonina,Maria",
    "Florian,Grzegorz,January","Irena,Ita,Pius","Benedykta,Benita,Dytrych",
    "Benedykt,Bogumir,Domicela","Dezyderia,Ilza,Marek","Beatus,Bożydar,Grzegorz",
    "Antonin,Częstomir,Izydor","Adalbert,Benedykt,Filip","Domicela,Domicjan,Dominik",
    "Andrzej,Aron,Ciechosław","Bończa,Bonifacy,Dobiesław","Afanazy,Atanazy,Berta",
    "Andrzej,Honorat,Jan Nepomucen","Bruno,Herakliusz,Paschalis","Aleksander,Aleksandra,Alicja",
    "Augustyn,Celestyn,Iwo","Anastazy,Asteriusz,Bazyli","Donat,Donata,Jan",
    "Emil,Helena,Jan","Budziwoj,Dezyderiusz,Dezydery","Cieszysława,Estera,Jan",
    "Epifan,Grzegorz,Imisława","Beda,Filip,Marianna","Beda,Izydor,Jan",
    "Augustyn,German,Jaromir","Bogusława,Maksymilian,Maria Magdalena","Andonik,Feliks,Ferdynand",
    "Aniela,Bożysława,Ernesta","Alfons,Alfonsyna,Bernard","Efrem,Erazm,Eugeniusz",
    "Cecyliusz,Ferdynand,Klotylda","Bazyliusz,Dacjan,Franciszek","Bończa,Bonifacy,Dobrociech",
    "Benignus,Dominika,Klaudiusz","Antoni,Ciechomir,Jarosław","Karp,Maksym,Medard",
    "Felicjan,Pelagia,Pelagiusz","Bogumił,Edgar,Małgorzata","Anastazy,Barnaba,Feliks",
    "Antonina,Bazyli,Jan","Antoni,Chociemir,Herman","Bazylid,Bazylis,Eliza",
    "Abraham,Angelina,Bernard","Alina,Aneta,Benon","Adolf,Adolfa,Adolfina",
    "Efrem,Elżbieta,Gerwazy","Borzysław,Gerwazy,Julianna","Bogna,Bogumiła,Bożena",
    "Albaniusz,Alicja,Alojza","Achacjusz,Achacy,Agenor","Agrypina,Albin,Bazyli",
    "Dan,Danisz,Danuta","Albrecht,Eulogiusz,Lucja","Jan,Jeremi,Jeremiasz",
    "Maria Magdalena,Władysław,Władysława","Amos,Ireneusz,Józef","Benedykta,Benita,Dalebor",
    "Alpinian,Ciechosława,Cyryl","Aaron,Bogusław,Halina","Juda,Maria,Martynian",
    "Anatol,Jacek,Korneli","Ageusz,Alfred,Aurelian","Antoni,Bartłomiej,Filomena",
    "Agrypina,Chociebor,Dominik","Antoni,Benedykt,Cyryl","Adrian,Adrianna,Chwalimir",
    "Anatolia,Heloiza,Hieronim","Aleksander,Amelia,Aniela","Benedykt,Cyprian,Kalina",
    "Andrzej,Euzebiusz,Feliks","Ernest,Ernestyn,Eugeniusz","Bonawentura,Damian,Dobrogost",
    "Daniel,Dawid,Dawida","Andrzej,Benedykt,Dziersław","Aleksander,Aleksy,Andrzej",
    "Arnold,Arnolf,Erwin","Alfred,Arseniusz,Lutobor","Czech,Czechasz,Czechoń",
    "Andrzej,Benedykt,Daniel","Albin,Bolesława,Bolisława","Apolinary,Bogna,Żelisław",
    "Antoni,Kinga,Krystyna","Jakub,Krzysztof,Nieznamir","Anna,Bartolomea,Grażyna",
    "Alfons,Alfonsyna,Aureli","Innocenta,Innocenty,Marcela","Beatrice,Beatrycze,Beatryks",
    "Abdon,Julia,Julita","Beatus,Demokryt,Emilian","Brodzisław,Justyn,Konrad",
    "Alfons,Alfonsyna,Borzysława","August,Augusta,Krzywosąd","Alfred,Arystarch,Dominik",
    "Cyriak,Emil,Karolin","Felicysym,Jakub,January","Albert,Alberta,Albertyna",
    "Cyprian,Cyriak,Cyryl","Jan,Klarysa,Miłorad","Asteria,Bernard,Bogdan",
    "Aleksander,Herman,Ligia","Bądzisław,Hilaria,Klara","Diana,Dianna,Gertruda",
    "Alfred,Atanazja,Dobrowój","Maria,Napoleon,Stefan","Alfons,Alfonsyna,Ambroży",
    "Anastazja,Angelika,Anita","Agapit,Bogusława,Bronisław","Bolesław,Emilia,Jan",
    "Bernard,Jan,Sabin","Adolf,Adolfa,Adolfina","Cezary,Dalegor,Fabrycjan",
    "Apolinary,Benicjusz,Filip","Bartłomiej,Cieszymir,Jerzy","Gaudencjusz,Gaudenty,Grzegorz",
    "Dobroniega,Joanna,Konstanty","Angel,Angelus,Cezary","Adelina,Aleksander,Aleksy",
    "Flora,Jan,Racibor","Adaukt,Częstowoj,Gaudencja","Bohdan,Paulina,Rajmund",
    "Bronisław,Bronisława,Bronisz","Absalon,Bohdan,Czech","Antoni,Bartłomiej,Bazylissa",
    "Agatonik,Ida,Lilianna","Dorota,Herakles,Herkulan","Albin,Beata,Eugenia",
    "Domasława,Domisława,Marek","Adrian,Adrianna,Klementyna","Augustyna,Aureliusz,Dionizy",
    "Aldona,Łukasz,Mikołaj","Feliks,Jacek,Jan","Amadeusz,Amedeusz,Cyrus",
    "Aleksander,Aureliusz,Eugenia","Bernard,Cyprian,Roksana","Albin,Budzigniew,Maria",
    "Antym,Cyprian,Edda","Ariadna,Dezyderiusz,Drogosław","Dobrowit,Irena,Irma",
    "Alfons,Alfonsyna,January","Dionizy,Eustachiusz,Eustachy","Bożeciech,Bożydar,Hipolit",
    "Joachim,Joachima,Maurycy","Boguchwała,Bogusław,Libert","Gerard,Gerarda,Gerhard",
    "Aureli,Aurelia,Aurelian","Cyprian,Euzebiusz,Justyna","Amadeusz,Amedeusz,Damian",
    "Jan,Laurencjusz,Luba","Dadźbog,Franciszek,Michalina","Grzegorz,Hieronim,Honoriusz",
    "Benigna,Cieszysław,Dan","Dionizy,Leodegar,Stanimir","Eustachiusz,Eustachy,Ewald",
    "Edwin,Franciszek,Konrad","Apolinary,Częstogniew,Donat","Artur,Artus,Bronisław",
    "Amalia,Justyna,Marek","Artemon,Bryda,Brygida","Arnold,Arnolf,Atanazja",
    "Franciszek,German,Kalistrat","Aldona,Brunon,Burchard","Cyriak,Eustachiusz,Eustachy",
    "Daniel,Edward,Gerald","Alan,Bernard,Dominik","Brunon,Gościsława,Jadwiga",
    "Ambroży,Aurelia,Dionizy","Lucyna,Małgorzata,Marian","Julian,Łukasz,René",
    "Ferdynand,Fryda,Pelagia","Budzisława,Irena,Jan Kanty","Bernard,Celina,Dobromił",
    "Abercjusz,Filip,Halka","Iga,Ignacja,Ignacy","Antoni,Boleczest,Filip",
    "Bończa,Bonifacy,Chryzant","Dymitriusz,Ewaryst,Eweryst","Frumencjusz,Iwona,Sabina",
    "Juda,Szymon,Tadeusz","Euzebia,Franciszek,Longin","Alfons,Alfonsyna,Angel",
    "Alfons,Alfonsyna,Antoni","Andrzej,Konradyn,Konradyna","Ambroży,Bohdana,Bożydar",
    "Bogumił,Cezary,Chwalisław","Emeryk,Karol Boromeusz,Mściwój","Blandyn,Blandyna,Dalemir",
    "Feliks,Leonard,Trzebowit","Achilles,Antoni,Engelbert","Dymitr,Godfryd,Gotfryd",
    "Bogudar,Genowefa,Nestor","Andrzej,Lena,Leon","Anastazja,Bartłomiej,Maciej",
    "Cibor,Czcibor,Izaak","Arkadiusz,Arkady,Brykcjusz","Aga,Agata,Damian",
    "Albert,Alberta,Albertyna","Aureliusz,Dionizy,Edmund","Dionizy,Floryn,Grzegorz",
    "Aniela,Cieszymysł,Filipina","Elżbieta,Mironiega,Paweł","Anatol,Edmund,Feliks",
    "Albert,Alberta,Albertyna","Cecylia,Marek,Maur","Adela,Erast,Felicyta",
    "Dobrosław,Emilia,Emma","Erazm,Jozafat,Katarzyna","Delfin,Dobiemiest,Jan",
    "Damazy,Dominik,Leonard","Gościrad,Grzegorz,Jakub","Błażej,Bolemysł,Fryderyk",
    "Andrzej,Justyna,Konstanty","Długosz,Edmund,Eliga","Adria,Aurelia,Balbina",
    "Franciszek,Kasjan,Ksawery","Barbara,Berno,Biernat","Anastazy,Gerald,Geraldyna",
    "Dionizja,Emilian,Jarema","Agaton,Ambroży,Marcin","Boguwola,Klement,Maria",
    "Delfina,Joachim,Joachima","Andrzej,Daniel,Judyta","Damazy,Daniela,Julia",
    "Adelajda,Aleksander,Dagmara","Lucja,Łucja,Otylia","Alfred,Arseniusz,Izydor",
    "Celina,Fortunata,Iga","Adelajda,Ado,Albina","Florian,Jolanta,Łazarz",
    "Bogusław,Gracjan,Gracjana","Abraham,Beniamin,Dariusz","Amon,Bogumiła,Dominik",
    "Balbin,Festus,Honorat","Beata,Drogomir,Flawian","Dagobert,Mina,Sławomir",
    "Ada,Adam,Adamina","Anastazja,Eugenia,Piotr","Dionizy,Szczepan,Wróciwoj",
    "Cezary,Fabia,Fabiola","Antoni,Dobrowiest,Emma","Domawit,Dominik,Gosław",
    "Dawid,Dawida,Dionizy","Korneliusz,Mariusz,Melania",
]
DAYS_IN_MONTH = [0,31,28,31,30,31,30,31,31,30,31,30,31]

def nameday_index(month, day):
    idx = sum(DAYS_IN_MONTH[m] for m in range(1, month)) + day - 1
    total = sum(DAYS_IN_MONTH)
    return min(idx, total - 1)

def short_date(now):
    return f"{now.day} {MONTH_PL[now.month-1]} {now.year}"

def nameday_text(now):
    idx = nameday_index(now.month, now.day)
    if 0 <= idx < len(NAMEDAYS):
        names = NAMEDAYS[idx].replace(",", ", ")
        return f"Imieniny: {names}"
    return ""

def nameday_names_only(now):
    idx = nameday_index(now.month, now.day)
    if 0 <= idx < len(NAMEDAYS):
        return NAMEDAYS[idx].replace(",", ", ")
    return ""

DAYS_PL = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]

def weekday_pl(now):
    return DAYS_PL[now.weekday()].lower()

# ---- RS485 Driver ----
ADDR = "37 37"  # display 29

def hex_byte(v):
    return format(v, '02X')

def hex_char(nib):
    nib &= 0xF
    v = 0x30 + nib if nib < 10 else 0x37 + nib
    return f"{v:02X}"

def make_message(text, font=3, line=0, alignment=1, x=0, w=96, scroll=0):
    """Build full hex frame string for one display command."""
    tx = " ".join(c.encode("cp852").hex() for c in text)
    text_count = len(text)
    data_len = text_count + 12
    lh = hex(data_len)[2:].upper().zfill(2)
    length = lh[0].encode("cp852").hex() + " " + lh[1].encode("cp852").hex()
    fb = hex_char(font - 1)
    lb = hex_char(1 if line else 0)
    ab = hex_char(0 if alignment == 0 else (1 if alignment == 1 else 2))
    xh = hex_char(x // 16)
    xl = hex_char(x % 16)
    wh = hex_char(w // 16)
    wl = hex_char(w % 16)
    sh = hex_char(scroll // 16)
    sl = hex_char(scroll % 16)
    ctrl = f"38 30 {lb} {ab} 37 {fb} {xh} {xl} {wh} {wl} {sh} {sl}"
    content = f"{ADDR} {length} {ctrl} {tx}"
    ck = sum(int(v, 16) for v in content.split()) % 256
    ck_s = hex(ck)[2:].upper().zfill(2)
    ck_hex = ck_s[0].encode("cp852").hex() + " " + ck_s[1].encode("cp852").hex()
    return f"02 {content} {ck_hex} 03"

def send_raw(ser, frame):
    """Send a hex frame string over RS485 (auto-direction dongle, no RTS)."""
    if not ser:
        return f"SIM: {frame[:60]}... ({len(frame)} chars)"
    data = bytes.fromhex(frame)
    ser.write(data)
    ser.flush()
    return f"TX: {frame[:60]}..."

def clear_screen(ser, addr="37 37"):
    """Blank both lines using reference protocol (byte9=0x31, font=3)."""
    spaces = "                  "  # 18 spaces
    tx = " ".join(c.encode("cp852").hex() for c in spaces)
    for li in [0, 1]:
        lb = "31" if li else "30"
        data_len = len(spaces) + 12
        lh = hex(data_len)[2:4].upper().zfill(2)
        length = lh[0].encode("cp852").hex() + " " + lh[1].encode("cp852").hex()
        ctrl = f"38 30 {lb} 30 31 32 30 30 36 30 30 30"
        content = f"{addr} {length} {ctrl} {tx}"
        ck = sum(int(v, 16) for v in content.split()) % 256
        ck_s = hex(ck)[2:].upper().zfill(2)
        ck_hex = ck_s[0].encode("cp852").hex() + " " + ck_s[1].encode("cp852").hex()
        frame = f"02 {content} {ck_hex} 03"
        send_raw(ser, frame)
        time.sleep(0.05)

send_blank = clear_screen

# ---- Preset expanders ----
def expand_preset(msg):
    """
    Expand a MessageSlot dict into a list of (text, font, line, align, x, w, scroll) tuples.
    This controls what the display actually shows.
    """
    preset = msg.get("preset_id", "custom")
    parts = []

    if preset == "scrolling":
        return [(msg["text"], msg.get("font", 1), msg.get("line", 0),
                 msg.get("alignment", 1), msg.get("pos_x", 0),
                 msg.get("width", 96), msg.get("scroll", 99))]

    elif preset == "single-static":
        return [(msg["text"], msg.get("font", 1), msg.get("line", 0),
                 msg.get("alignment", 0), msg.get("pos_x", 0),
                 msg.get("width", 96), 0)]

    elif preset == "two-static":
        # Text format: "Line1||Line2"
        lines = msg.get("text", "").split("||")
        if len(lines) >= 1 and lines[0].strip():
            parts.append((lines[0].strip(), 1, 0, 0, 0, 96, 0))
        if len(lines) >= 2 and lines[1].strip():
            parts.append((lines[1].strip(), 1, 1, 0, 0, 96, 0))
        return parts

    elif preset == "bus":
        # Route (font 3, left) + dest (font 1, same line) + scrolling (L1)
        # Bytes 11-12 (dest X) shift right based on route pixel width + manual shift.
        # Digit widths: '1'=4px, others=6px, 1px gap between chars.
        route = msg.get("text", "")
        dest = msg.get("name", "")
        scroll_txt = msg.get("_scroll", "")
        shift = msg.get("_bus_shift", 0)
        if route:
            w = sum(4 if c == '1' else 6 for c in route) + max(0, len(route) - 1)
            dest_x = max(6, min(60, 2 + w + 2 + shift))
            parts.append((route, 3, 0, 0, 2, dest_x - 1, 0))
        else:
            dest_x = 6
        if dest:
            parts.append((dest, 1, 0, 0, dest_x, 96, 0))
        if scroll_txt:
            sc = msg.get("scroll", 99)
            parts.append((scroll_txt, 1, 1, 2, dest_x, 96, sc))
        return parts

    elif preset == "train":
        # From-station (L0 left) + to-station (L1 right) + number (L0 right, font 5)
        # Display is 88px wide. Number right-aligned with 4px right margin.
        # Digit sizes: all 4px, 1px gap between chars. nw = len*5 - 1.
        from_st = msg.get("text", "")
        to_st = msg.get("_train_to", "")
        number = msg.get("name", "")
        f_from = msg.get("_train_font_from", 1)
        f_to = msg.get("_train_font_to", 1)
        a_from = msg.get("_train_align_from", 0)
        a_to = msg.get("_train_align_to", 2)
        shift = msg.get("_train_shift", 0)
        if number:
            nw = len(number) * 5 - 1  # 4px/digit + 1px gaps
            num_x = max(20, min(80, 84 - nw + shift))
            st_right = num_x
            if from_st:
                parts.append((from_st, f_from, 0, a_from, 2, st_right, 0))
            if to_st:
                parts.append((to_st, f_to, 1, a_to, 0, st_right, 0))
            parts.append((number, 5, 0, 0, num_x, 96, 0))
        else:
            if from_st:
                parts.append((from_st, f_from, 0, a_from, 2, 96, 0))
            if to_st:
                parts.append((to_st, f_to, 1, a_to, 0, 96, 0))
        return parts

    elif preset == "top-bottom-scroll":
        top = msg.get("text", "")
        bottom = msg.get("_tbs_bottom", "")
        ft = msg.get("_tbs_font_top", 1)
        fb = msg.get("_tbs_font_bottom", 1)
        sc = msg.get("_tbs_scroll", 99)
        if top:
            parts.append((top, ft, 0, 1, 0, 96, 0))
        if bottom:
            parts.append((bottom, fb, 1, 1, 0, 96, sc))
        return parts

    elif preset == "clock":
        # Time (font 3, line 0, left) + date (font 1, line 0, after time) + Polish weekday (line 1)
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        # Pixel widths: '1'=4px, others=6px, ':'=4px, 1px gaps
        time_width = sum(4 if c == '1' else (2 if c == ':' else 6) for c in time_str) + len(time_str) - 1
        shift = msg.get("_clock_shift", 0)
        time_right = max(6, min(60, 2 + time_width + 2 + shift))
        parts.append(("__clock_time__", 3, 0, 0, 2, time_right, 0))
        date_x = time_right + 4
        parts.append(("__clock_date__", 1, 0, 0, date_x, 96, 0))
        if msg.get("_clock_namedays", True):
            date_text = short_date(now)
            weekday_text = weekday_pl(now)
            f1_pw = lambda t: 4 * len(t)
            weekday_x = date_x + max(0, (f1_pw(date_text) - f1_pw(weekday_text)) // 2)
            parts.append(("__clock_weekday__", 1, 1, 0, weekday_x, 96, 0))
        return parts

    elif preset == "imieniny":
        sc = int(msg.get("_imieniny_scroll", 99))
        parts.append(("IMIENINY", 2, 0, 1, 0, 96, 0))
        parts.append(("__imieniny_names__", 1, 1, 1, 0, 96, sc))
        return parts

    else:  # custom
        return [(msg.get("text", ""), msg.get("font", 1), msg.get("line", 0),
                 msg.get("alignment", 0), msg.get("pos_x", 0),
                 msg.get("width", 96), msg.get("scroll", 0))]

def fill_dynamic(text):
    """Replace __clock_time__ / __clock_date__ / __clock_nameday__ with actual values."""
    from datetime import datetime
    now = datetime.now()
    if text == "__clock_time__":
        return now.strftime("%H:%M")
    if text == "__clock_date__":
        return short_date(now)
    if text == "__clock_weekday__":
        return weekday_pl(now)
    if text == "__imieniny_names__":
        return nameday_names_only(now)
    if text == "__dynamic__":
        return " "
    return text

def send_preset(ser, msg, gap_ms=100):
    """Send a complete preset (may be multiple display commands) with gaps."""
    parts = expand_preset(msg)
    logs = []
    for text, font, line, align, x, w, scroll in parts:
        t = fill_dynamic(text)
        if t == "" and text.startswith("__"):
            t = " "  # fallback if dynamic filler fails
        frame = make_message(t, font, line, align, x, w, scroll)
        r = send_raw(ser, frame)
        logs.append(r)
        if len(parts) > 1:
            time.sleep(gap_ms / 1000.0)
    return "; ".join(logs)

# ---- WebUI HTML ----
_HERE = os.path.dirname(__file__)
HTML_FILE = os.path.join(_HERE, "webui.html")

def load_html():
    with open(HTML_FILE) as f:
        return f.read()

# ---- State ----
class State:
    def __init__(self):
        self.messages = []
        self.settings = {
            "display_number": 29,
            "preset_gap_ms": 100,
            "keepalive_sec": 60,
            "queue_running": True,
        }
        self.override = {"active": False, "message": {}, "expires_at": 0}
        self.queue_pos = 0
        self.queue_thread_running = False
        self.serial = None

    def next_id(self):
        import uuid
        return str(uuid.uuid4())[:8]

state = State()

def queue_loop():
    while state.queue_thread_running:
        if not state.settings["queue_running"] or state.override.get("active"):
            time.sleep(1)
            continue
        visible = [m for m in state.messages if not m.get("hidden")]
        if not visible:
            time.sleep(1)
            continue
        if state.queue_pos >= len(state.messages):
            state.queue_pos = 0
        msg = state.messages[state.queue_pos]
        if msg.get("hidden"):
            state.queue_pos += 1
            continue
        # Between messages: blank first
        send_blank(state.serial)
        time.sleep(0.05)
        send_preset(state.serial, msg, state.settings.get("preset_gap_ms", 100))
        state.last_display = time.time()
        dur = msg.get("duration_sec", 30)
        state.queue_pos += 1
        time.sleep(dur)

# ---- HTTP ----
class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.html = kwargs.pop("html", "")
        super().__init__(*args, **kwargs)

    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        p = urlparse(self.path).path.rstrip("/")
        if p in ("", "/"):
            return self._html(self.html)
        elif p == "/api/status":
            self._json({
                "ok": True,
                "display_connected": state.serial is not None,
                "queue_running": state.settings["queue_running"],
                "queue_position": state.queue_pos,
                "messages_count": len(state.messages),
                "override_active": state.override.get("active", False),
                "time_synced": getattr(state, '_synced_time', 0) > 0,
                "settings": state.settings,
            })
        elif p == "/api/messages":
            self._json({"messages": state.messages})
        elif p == "/api/settings":
            self._json(state.settings)
        elif p == "/api/override":
            self._json(state.override)
        else:
            self._html(self.html)

    def do_POST(self):
        p = urlparse(self.path).path.rstrip("/")
        if p == "/api/messages":
            msg = self._body()
            if not msg.get("id"):
                msg["id"] = state.next_id()
            state.messages.append(msg)
            self._json(msg, 201)
        elif p == "/api/test":
            r = send_preset(state.serial, {"text": f"TEST {state.settings['display_number']}",
                "font": 3, "line": 0, "alignment": 1, "pos_x": 0, "width": 96, "scroll": 0,
                "preset_id": "single-static"}, gap_ms=100)
            self._json({"result": r})
        elif p == "/api/discover":
            self._json({"result": "Discovery only works on ESP (scans addresses 1-31)"})
        elif p == "/api/override":
            b = self._body()
            state.override = b
            if b.get("active") and b.get("message"):
                send_blank(state.serial)
                time.sleep(0.05)
                send_preset(state.serial, b["message"], state.settings.get("preset_gap_ms", 100))
            self._json(state.override)
        elif p == "/api/cancel-override":
            state.override = {"active": False, "message": {}, "expires_at": 0}
            self._json({"ok": True})
        elif p == "/api/clear":
            send_blank(state.serial)
            self._json({"ok": True})
        elif p == "/api/messages/reorder":
            b = self._body()
            ids = b.get("ids", [])
            lookup = {m.get("id"): m for m in state.messages}
            state.messages = [lookup[i] for i in ids if i in lookup]
            self._json({"ok": True})
        elif p == "/api/time":
            b = self._body()
            ts = b.get("unix_seconds", 0)
            if ts:
                import datetime
                state._synced_time = ts
                state._synced_time_offset = time.time() - ts
                print(f"Time synced: {ts} ({datetime.datetime.fromtimestamp(ts)})")
            self._json({"ok": True})
        elif p == "/api/skip-to-message":
            q = parse_qs(urlparse(self.path).query)
            mid = q.get("id", [None])[0]
            if not mid:
                return self._json({"error": "missing id"}, 400)
            for i, m in enumerate(state.messages):
                if m.get("id") == mid:
                    state.override = {"active": False, "message": {}, "expires_at": 0}
                    state.queue_pos = i
                    send_blank(state.serial)
                    time.sleep(0.05)
                    send_preset(state.serial, m, state.settings.get("preset_gap_ms", 100))
                    return self._json({"ok": True, "index": i})
            self._json({"error": "not found"}, 404)
        else:
            self._json({"error": "not found"}, 404)

    def do_PUT(self):
        p = urlparse(self.path).path.rstrip("/")
        q = parse_qs(urlparse(self.path).query)
        if p == "/api/messages":
            mid = q.get("id", [None])[0]
            if not mid:
                return self._json({"error": "missing id"}, 400)
            b = self._body()
            for i, m in enumerate(state.messages):
                if m.get("id") == mid:
                    b["id"] = mid
                    state.messages[i] = b
                    return self._json(b)
            self._json({"error": "not found"}, 404)
        elif p == "/api/settings":
            state.settings.update(self._body())
            self._json(state.settings)
        else:
            self._json({"error": "not found"}, 404)

    def do_DELETE(self):
        p = urlparse(self.path).path.rstrip("/")
        q = parse_qs(urlparse(self.path).query)
        if p == "/api/messages":
            mid = q.get("id", [None])[0]
            if not mid:
                return self._json({"error": "missing id"}, 400)
            state.messages = [m for m in state.messages if m.get("id") != mid]
            self._json({"ok": True})
        else:
            self._json({"error": "not found"}, 404)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=8080, type=int)
    ap.add_argument("--serial", default="/dev/cu.usbmodem5A7E0300181")
    args = ap.parse_args()

    try:
        ser = serial.Serial(args.serial, 9600, timeout=2)
        ser.rts = False
        time.sleep(0.3)
        state.serial = ser
        print(f"RS485 on {args.serial}")
    except Exception as e:
        print(f"No serial ({e}) — SIMULATION MODE")
        state.serial = None

    html = load_html()
    print(f"WebUI loaded ({len(html)} bytes)")

    state.queue_thread_running = True
    threading.Thread(target=queue_loop, daemon=True).start()

    handler = partial(Handler, html=html)
    srv = HTTPServer(("0.0.0.0", args.port), handler)
    print(f"Server: http://localhost:{args.port}/")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        state.queue_thread_running = False
        if state.serial:
            state.serial.close()
        srv.server_close()

if __name__ == "__main__":
    main()
