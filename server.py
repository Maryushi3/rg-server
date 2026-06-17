#!/usr/bin/env python3
"""
RG Display Server — local RS485 controller for R&G LED displays.
Run: python server.py [--port 8080] [--serial /dev/...]
"""
import argparse, json, math, os, re, serial, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from functools import partial

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "messages.json")
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

# ---- Clock Data (mirrors clock.hpp) ----
MONTH_PL = ["sty","lut","mar","kwi","maj","cze","lip","sie","wrz","paź","lis","gru"]
NAMEDAYS = [
    "Masław,Mieczysław,Mieczysława,Konkordiusz,Mieszko",
    "Abel,Izydor,Makary,Achacy,Achacjusz",
    "Arletta,Dan,Danisz,Anter,Arleta",
    "Angelika,Aniela,Benedykta,Dobromir,Eugeniusz",
    "Edward,Emilian,Emiliusz,Emiliana,Piotr",
    "Andrzej,Balcer,Baltazar,Jędrzej,Bolemir",
    "Chociesław,Izydor,Julian,Kryspin,Lucjan",
    "Erhard,Mścisław,Seweryn,Heladiusz",
    "Antoni,Bazylissa,Borzymir,Adrian,Bazylisa",
    "Agaton,Dobrosław,Jan,Anna,Hanna",
    "Feliks,Hilary,Honorata,Gracja,Hortensja",
    "Antoni,Arkadiusz,Arkady,Benedykt,Cezaria",
    "Bogumił,Bogusąd,Bogusława,Godfryd,Leoncjusz",
    "Feliks,Hilary,Odo,Amadeusz,Amadea",
    "Aleksander,Dąbrówka,Dobrawa,Domasław,Eligia",
    "Marcel,Waleriusz,Włodzimierz,Piotr,Treweriusz",
    "Antoni,Jan,Rościsław,Alba,Przemił",
    "Bogumił,Jaropełk,Krystyna,Liberata,Lubart",
    "Andrzej,Bernard,Erwin,Adalryk,Alderyk",
    "Dobiegniew,Fabian,Sebastian,Dobrożyźń",
    "Agnieszka,Epifani,Jarosław,Awit,Awita",
    "Anastazy,Dobromysł,Gaudencjusz,Gaudenty,Jutrogost",
    "Emerencja,Ildefons,Jan,Klemens,Maria",
    "Chwalibóg,Felicja,Mirogniew,Chwalibog,Franciszek Salezy",
    "Miłosz,Miłowan,Miłowit,Apollo(n),Artemia",
    "Paula,Paulina,Polikarp,Ksenofont,Leon",
    "Angelika,Ilona,Jan Chryzostom,Adalruna,Alruna",
    "Agnieszka,Augustyn,Flawian,Ildefons,Julian",
    "Franciszek Salezy,Gilda,Hanna,Bartłomiej,Gildas",
    "Adelajda,Feliks,Gerard,Adalgunda,Adelgunda",
    "Cyrus,Euzebiusz,Jan,Eudoksja,Heloiza",
    "Bryda,Brygida,Dobrocha,Emil,Paweł",
    "Joanna,Korneliusz,Maria,Berwin,Ermentruda",
    "Błażej,Hipolit,Hipolita,Ignacy,Klaudyna",
    "Andrzej,Gilbert,Jan,Jędrzej,Częstogoj",
    "Adelajda,Aga,Agata,Albwin,Elpin",
    "Angel,Angelus,Antoni,Amand,Amanda",
    "Romuald,Ryszard,Sulisław,Alfons,Parteniusz",
    "Gniewomir,Gniewosz,Honorat,Ampeliusz,Ampelia",
    "Apolonia,Bernard,Cyryl,Eryk,Eryka",
    "Elwira,Gabriel,Jacek,Apollo(n),Jacenty",
    "Adolf,Adolfa,Adolfina,Bernadeta,Bertrada",
    "Aleksy,Benedykt,Eulalia,Ampeliusz,Ampelia",
    "Benigna,Grzegorz,Jordan,Humbelina,Jordana",
    "Adolf,Adolfa,Adolfina,Auksencjusz,Auksencja",
    "Faustyn,Georgia,Georgina,Jordan,Jordana",
    "Bernard,Dan,Danisz,Daniel,Danuta",
    "Donat,Donata,Franciszek,Julian,Klemens",
    "Albert,Alberta,Albertyna,Agapita,Gertruda",
    "Arnold,Arnolf,Bądzisława,Barbacy,Barbat",
    "Euchariusz,Eustachiusz,Eustachy,Aulus,Leon",
    "Eleonora,Feliks,Fortunat,Gumbert,Henryka",
    "Małgorzata,Nikifor,Piotr,Chociebąd,Konkordia",
    "Bądzimir,Damian,Florentyn,Łazarz,Marta",
    "Bogurad,Bogusz,Boguta,Ermegarda,Irmegarda",
    "Bolebor,Cezary,Konstancjusz,Adam,Antonina",
    "Aleksander,Bogumił,Cezariusz,Dionizy,Gerlinda",
    "Aleksander,Anastazja,Auksencjusz,Achacy,Achacjusz",
    "Chwalibóg,Józef,Makary,Falibog,Gajusz",
    "Albin,Antoni,Antonina,August,Budzisław",
    "Absalon,Franciszek,Halszka,Agnieszka,Helena",
    "Asteriusz,Hieronim,Kunegunda,Gerwin,Gerwina",
    "Adrian,Adrianna,Arkadiusz,Arkady,Jakobina",
    "Adrian,Adrianna,Fryderyk,Jan,Jeremiasz",
    "Eugenia,Felicyta,Frydolin,Będzimysł,Jordan",
    "Felicja,Nadmir,Paweł,Bazyli,Eubul",
    "Beata,Filemon,Jan,Herenia,Julian",
    "Apollo,Dominik,Franciszka,Katarzyna,Mścisława",
    "Aleksander,Bożysław,Cyprian,Gajusz,Kajus",
    "Benedykt,Drogosława,Edwin,Kandyd,Konstanty",
    "Bernard,Blizbor,Grzegorz,Józefina,Piotr",
    "Bożena,Ernest,Ernestyn,Bratomir,Kasjan",
    "Bożeciecha,Jakub,Leon,Afrodyzjusz,Afrodyzy",
    "Gościmir,Heloiza,Klemens,Krzysztof,Longin",
    "Abraham,Cyriak,Henryka,Artemia,Herbert",
    "Gertruda,Harasym,Jan,Agrykola,Gerazym",
    "Aleksander,Anzelm,Boguchwał,Celestyna,Cyryl",
    "Bogdan,Józef,Marek,Markusław,Sybillina",
    "Aleksander,Aleksandra,Ambroży,Anatol,Archip",
    "Benedykt,Filemon,Lubomira,Justynian,Klemencja",
    "Bazylissa,Bogusław,Godzisław,August,Baldwin",
    "Eberhard,Feliks,Katarzyna,Oktawian,Pelagia",
    "Dziersława,Dzierżysława,Gabor,Ademar,Aldmir",
    "Dyzma,Ireneusz,Łucja,Dula,Jozafata",
    "Emanuel,Feliks,Larysa,Bazyli,Emanuela",
    "Benedykt,Ernest,Ernestyn,Jan,Lidia",
    "Aniela,Antoni,Jan,Joanna,Kastor",
    "Cyryl,Czcirad,Eustachiusz,Eustachy,Marek",
    "Amelia,Aniela,Częstobor,Amadeusz,Amadea",
    "Amos,Balbina,Beniamin,Achacy,Achacjusz",
    "Chryzant,Grażyna,Hugo,Hugon,Jakobina",
    "Franciszek,Sądomir,Urban,Laurencja,Miłobąd",
    "Antoni,Cieszygor,Jakub,Pankracy,Ryszard",
    "Ambroży,Bazyli,Benedykt,Izydor,Mira",
    "Borzywoj,Irena,Wincenty",
    "Ada,Adam,Adamina,Celestyn,Celestyna",
    "Donat,Donata,Epifaniusz,Hegezyp,Herman",
    "Apolinary,Cezary,Cezaryna,August,Dionizy",
    "Dobrosława,Dymitr,Maja,Achacy,Achacjusz",
    "Antoni,Apoloniusz,Daniel,Ezechiel,Grodzisław",
    "Filip,Herman,Jaromir,Gemma,Hildebrand",
    "Andrzej,Iwan,Juliusz,Jędrzej,Sabbas",
    "Hermenegild,Hermenegilda,Ida,Długomił,Jan",
    "Berenike,Julianna,Justyn,Ardalion,Justyna",
    "Anastazja,Bazyli,Leonid,Abel,Modest",
    "Benedykt,Bernadetta,Cecyl,Bernadeta,Cecylian",
    "Anicet,Innocenta,Innocenty,Aniceta,Izydor",
    "Apoloniusz,Bogusław,Bogusława,Alicja,Barbara",
    "Adolf,Adolfa,Adolfina,Cieszyrad,Irydion",
    "Agnieszka,Amalia,Czech,Berenika,Czasław",
    "Addar,Anzelm,Bartosz,Apollina,Apollo(n)",
    "Heliodor,Kajus,Leonia,Agapita,Aital",
    "Adalbert,Gerard,Gerarda,Gabriela,Helena",
    "Aleksander,Aleksy,Egbert,Aleksja,Erwin",
    "Jarosław,Marek,Wasyl,Ewodiusz,Ewodia",
    "Artemon,Klaudiusz,Klet,Klarencjusz,Marcelin",
    "Anastazy,Andrzej,Bożebor,Jędrzej,Felicja",
    "Arystarch,Maria,Paweł,Achacy,Achacjusz",
    "Angelina,Augustyn,Bogusław,Ermentruda,Hugo",
    "Bartłomiej,Chwalisława,Eutropiusz,Afrodyzjusz,Afrodyzy",
    "Aniela,Filip,Jakub,Floryna,Jeremi",
    "Afanazy,Anatol,Atanazy,Borys,Walenty",
    "Aleksander,Antonina,Maria,Alodia,Juwenalis",
    "Florian,Grzegorz,January,Antonina,Michał",
    "Irena,Ita,Pius,Penelopa,Stanisław",
    "Benedykta,Benita,Dytrych,Domagniew,Edbert",
    "Benedykt,Bogumir,Domicela,August,Domicjan",
    "Dezyderia,Ilza,Marek,Achacy,Achacjusz",
    "Beatus,Bożydar,Grzegorz,Beat,Karolina",
    "Antonin,Częstomir,Izydor,Chociesław,Gordian",
    "Adalbert,Benedykt,Filip,Franciszek,Iga",
    "Domicela,Domicjan,Dominik,Domicjana,Epifani",
    "Andrzej,Aron,Ciechosław,Agnieszka,Jędrzej",
    "Bończa,Bonifacy,Dobiesław,Ampeliusz,Ampelia",
    "Afanazy,Atanazy,Berta,Cecyliusz,Czcibora",
    "Andrzej,Honorat,Jan Nepomucen,Adam,Jędrzej",
    "Bruno,Herakliusz,Paschalis,Montan,Sławomir",
    "Aleksander,Aleksandra,Alicja,Eryk,Feliks",
    "Augustyn,Celestyn,Iwo,Bernarda,Iwon",
    "Anastazy,Asteriusz,Bazyli,Bazylides,Bernardyn",
    "Donat,Donata,Jan,Krzysztof,Piotr",
    "Emil,Helena,Jan,Julia,Krzesisława",
    "Budziwoj,Dezyderiusz,Dezydery,Emilia,Eufrozyna",
    "Cieszysława,Estera,Jan,Joanna,Maria",
    "Epifan,Grzegorz,Imisława,Beda,Leon",
    "Beda,Filip,Marianna,Adalwin,Adalwina",
    "Beda,Izydor,Jan,Juliusz,Lucjan",
    "Augustyn,German,Jaromir,Emil,Heladiusz",
    "Bogusława,Maksymilian,Maria Magdalena,Ermentruda,Magdalena",
    "Andonik,Feliks,Ferdynand,Andronik,Bazyli",
    "Aniela,Bożysława,Ernesta,Ernestyna,Feliks",
    "Alfons,Alfonsyna,Bernard,Felin,Felina",
    "Efrem,Erazm,Eugeniusz,Domna,Florianna",
    "Cecyliusz,Ferdynand,Klotylda,Karol,Konstantyn",
    "Bazyliusz,Dacjan,Franciszek,Braturad,Gostmił",
    "Bończa,Bonifacy,Dobrociech,Hildebrand,Hildebranda",
    "Benignus,Dominika,Klaudiusz,Kandyda,Laurenty",
    "Antoni,Ciechomir,Jarosław,Anna,Hanna",
    "Karp,Maksym,Medard,Adriana,Medarda",
    "Felicjan,Pelagia,Pelagiusz,Anna,Hanna",
    "Bogumił,Edgar,Małgorzata,Apollo(n),Bogumiła",
    "Anastazy,Barnaba,Feliks,Radomił,Teodozja",
    "Antonina,Bazyli,Jan,Celestyna,Czesław",
    "Antoni,Chociemir,Herman,Lubowid,Lucjan",
    "Bazylid,Bazylis,Eliza,Bazylides,Justyn",
    "Abraham,Angelina,Bernard,Dula,Edburga",
    "Alina,Aneta,Benon,Aubert,Aureusz",
    "Adolf,Adolfa,Adolfina,Adrianna,Awit",
    "Efrem,Elżbieta,Gerwazy,Amand,Amanda",
    "Borzysław, Gerwazy, Julianna, Eurydyka, Grymilda oraz Michalina, Odo, Protazy, Abraham, Adam, Adrian, Agata, Agnieszka, Alan, Albert, Albin, Aldona, Aleksander, Aleksandra, Alfred, Amadeusz, Amelia, Anastazja, Andrzej",
    "Bogna, Bogumiła, Bożena, Bratomir, Edburga oraz Florentyna, Franciszek, Gemma, Hektor, Jaktor, Michał, Rafał, Abraham, Adam, Adrian, Agata, Agnieszka, Alan, Albert, Albin, Aldona, Aleksander, Aleksandra, Alfred",
    "Albaniusz, Alicja, Alojza, Alojzy, Chloe oraz Demetria, Domamir, Lutfryd, Rudolf, Rudolfa, Rudolfina, Teodor, Abraham, Adam, Adrian, Agata, Agnieszka, Alan, Albert, Albin, Aldona, Aleksander, Aleksandra, Alfred",
    "Achacjusz,Achacy,Agenor,Alban,Flawiusz",
    "Agrypina,Albin,Bazyli,Anna,Hanna",
    "Dan,Danisz,Danuta,Emilia,Jan",
    "Albrecht,Eulogiusz,Lucja,Antyd,Dorota",
    "Jan,Jeremi,Jeremiasz,Dawid,Edburga",
    "Maria Magdalena,Władysław,Władysława,Bożydar,Cyryl",
    "Amos,Ireneusz,Józef,Ekard,Heron",
    "Benedykta,Benita,Dalebor,Kasjusz,Paweł",
    "Alpinian,Ciechosława,Cyryl,Bazyli,Emilia",
    "Aaron,Bogusław,Halina,Domicjan,Domicjana",
    "Juda,Maria,Martynian,Bernardyn,Bożydar",
    "Anatol,Jacek,Korneli,Heliodor,Leon",
    "Ageusz,Alfred,Aurelian,Aggeusz,Berta",
    "Antoni,Bartłomiej,Filomena,Jakub,Marta",
    "Agrypina,Chociebor,Dominik,Dominika,Gotard",
    "Antoni,Benedykt,Cyryl,German,Kira",
    "Adrian,Adrianna,Chwalimir,Adolf,Adolfa",
    "Anatolia,Heloiza,Hieronim,Adolfina,Anatola",
    "Aleksander,Amelia,Aniela,Amalberga,Askaniusz",
    "Benedykt,Cyprian,Kalina,Karina,Karyna",
    "Andrzej,Euzebiusz,Feliks,Jędrzej,Epifania",
    "Ernest,Ernestyn,Eugeniusz,Ezdrasz,Henryk",
    "Bonawentura,Damian,Dobrogost,Franciszek,Izabela",
    "Daniel,Dawid,Dawida,Anna,Hanna",
    "Andrzej,Benedykt,Dziersław,Jędrzej,Dzierżysław",
    "Aleksander,Aleksy,Andrzej,Aleksja,Jędrzej",
    "Arnold,Arnolf,Erwin,Arnulf,Matern",
    "Alfred,Arseniusz,Lutobor,Litobor,Marcin",
    "Czech,Czechasz,Czechoń,Czesław,Czesława",
    "Andrzej,Benedykt,Daniel,Jędrzej,Arbogast",
    "Albin,Bolesława,Bolisława,Laurencjusz,Magdalena",
    "Apolinary,Bogna,Żelisław,Apolinaria,Joanna",
    "Antoni,Kinga,Krystyna,Krzesimir,Kunegunda",
    "Jakub,Krzysztof,Nieznamir,Alfons,Dariusz",
    "Anna,Bartolomea,Grażyna,Anita,Hanna",
    "Alfons,Alfonsyna,Aureli,Julia,Laurenty",
    "Innocenta,Innocenty,Marcela,Achacy,Achacjusz",
    "Beatrice,Beatrycze,Beatryks,Cierpisław,Faustyn",
    "Abdon,Julia,Julita,Ludmiła,Maryna",
    "Beatus,Demokryt,Emilian,Adam,Alfonsa",
    "Brodzisław,Justyn,Konrad,Alfons,Justyna",
    "Alfons,Alfonsyna,Borzysława,Edeltruda,Gustaw",
    "August,Augusta,Krzywosąd,Dalmacjusz,Lidia",
    "Alfred,Arystarch,Dominik,Maria,Mironieg",
    "Cyriak,Emil,Karolin,Abel,Maria",
    "Felicysym,Jakub,January,Namir,Stefan",
    "Albert,Alberta,Albertyna,Andromeda,Dobiemir",
    "Cyprian,Cyriak,Cyryl,Dominik,Emilian",
    "Jan,Klarysa,Miłorad,Domicjan,Domicjana",
    "Asteria,Bernard,Bogdan,Amadeusz,Amadea",
    "Aleksander,Herman,Ligia,Lukrecja,Tyburcjusz",
    "Bądzisław,Hilaria,Klara,Bądzsław,Fotyn",
    "Diana,Dianna,Gertruda,Adriana,Helena",
    "Alfred,Atanazja,Dobrowój,Dobrowoj,Dobrowoja",
    "Maria,Napoleon,Stefan,Armida,Arnulf",
    "Alfons,Alfonsyna,Ambroży,Arsacjusz,Domarad",
    "Anastazja,Angelika,Anita,Bertram,Eliza",
    "Agapit,Bogusława,Bronisław,Helena,Ilona",
    "Bolesław,Emilia,Jan,Julian,Juliusz",
    "Bernard,Jan,Sabin,Samuel,Samuela",
    "Adolf,Adolfa,Adolfina,Agapiusz,Baldwin",
    "Cezary,Dalegor,Fabrycjan,Agatonik,Fabrycy",
    "Apolinary,Benicjusz,Filip,Klaudiusz,Laurenty",
    "Bartłomiej,Cieszymir,Jerzy,Anita,Bartosz",
    "Gaudencjusz,Gaudenty,Grzegorz,Arediusz,Elwira",
    "Dobroniega,Joanna,Konstanty,Maksym,Maria",
    "Angel,Angelus,Cezary,Adrianna,Amadeusz",
    "Adelina,Aleksander,Aleksy,Adelinda,Alfons",
    "Flora,Jan,Racibor,Mederyk,Mederyka",
    "Adaukt,Częstowoj,Gaudencja,Miron,Piotr",
    "Bohdan,Paulina,Rajmund,Albertyna,Amat",
    "Bronisław,Bronisława,Bronisz,Anna,Hanna",
    "Absalon,Bohdan,Czech,Adelina,Dionizy",
    "Antoni,Bartłomiej,Bazylissa,Bazylisa,Bronisław",
    "Agatonik,Ida,Lilianna,Bonifacy,Daniela",
    "Dorota,Herakles,Herkulan,Fereol,Herkules",
    "Albin,Beata,Eugenia,Aleksja,Amoniusz",
    "Domasława,Domisława,Marek,Dobrobąd,Gratus",
    "Adrian,Adrianna,Klementyna,Adam,Maria",
    "Augustyna,Aureliusz,Dionizy,Gorgoniusz,Grażyna",
    "Aldona,Łukasz,Mikołaj,Agapiusz,Kandyda",
    "Feliks,Jacek,Jan,Ademar,Dagna",
    "Amadeusz,Amedeusz,Cyrus,Gwidon,Maria",
    "Aleksander,Aureliusz,Eugenia,Amat,Filip",
    "Bernard,Cyprian,Roksana,Matern,Piotr",
    "Albin,Budzigniew,Maria,Ekard,Kamil",
    "Antym,Cyprian,Edda,Edyta,Eufemia",
    "Ariadna,Dezyderiusz,Drogosław,Cherubin,Franciszek",
    "Dobrowit,Irena,Irma,Ariadna,Baltazar",
    "Alfons,Alfonsyna,January,Arnulf,Arnolf",
    "Dionizy,Eustachiusz,Eustachy,Agnieszka,Barbara",
    "Bożeciech,Bożydar,Hipolit,Bernardyna,Ifigenia",
    "Joachim,Joachima,Maurycy,Ignacy,Józefa",
    "Boguchwała,Bogusław,Libert,Elżbieta,Krzysztof",
    "Gerard,Gerarda,Gerhard,Maria,Teodor",
    "Aureli,Aurelia,Aurelian,Ermenfryd,Irmfryd",
    "Cyprian,Euzebiusz,Justyna,Damian,Kacper",
    "Amadeusz,Amedeusz,Damian,Gajusz,Kajus",
    "Jan,Laurencjusz,Luba,Alodiusz,Amalia",
    "Dadźbog,Franciszek,Michalina,Dadzbog,Dadzboga",
    "Grzegorz,Hieronim,Honoriusz,Euzebia,Felicja",
    "Benigna,Cieszysław,Dan,Danuta,Igor",
    "Dionizy,Leodegar,Stanimir,Nasiębor,Teofil",
    "Eustachiusz,Eustachy,Ewald,Augustyna,Cyprian",
    "Edwin,Franciszek,Konrad,Dalewin,Dalwin",
    "Apolinary,Częstogniew,Donat,Charytyna,Faust",
    "Artur,Artus,Bronisław,Alberta,Askaniusz",
    "Amalia,Justyna,Marek,August,Markusław",
    "Artemon,Bryda,Brygida,Demetriusz,Ewodiusz",
    "Arnold,Arnolf,Atanazja,Aaron,Bogdan",
    "Franciszek,German,Kalistrat,Adalryk,Alderyk",
    "Aldona,Brunon,Burchard,Dobromiła,Emil",
    "Cyriak,Eustachiusz,Eustachy,Edwin,Grzymisław",
    "Daniel,Edward,Gerald,Florencjusz,Florenty",
    "Alan,Bernard,Dominik,Fortunata,Gajusz",
    "Brunon,Gościsława,Jadwiga,Sewer,Tekla",
    "Ambroży,Aurelia,Dionizy,Emil,Florentyna",
    "Lucyna,Małgorzata,Marian,Augustyna,Heron",
    "Julian,Łukasz,René,Piotr,Ziemowit",
    "Ferdynand,Fryda,Pelagia,Kleopatra,Paweł",
    "Budzisława,Irena,Jan Kanty,Apollo(n),Aurora",
    "Bernard,Celina,Dobromił,Elżbieta,Hilary",
    "Abercjusz,Filip,Halka,Alodia,Kordian",
    "Iga,Ignacja,Ignacy,German,Giedymin",
    "Antoni,Boleczest,Filip,Marcin,Marek",
    "Bończa,Bonifacy,Chryzant,Daria,Inga",
    "Dymitriusz,Ewaryst,Eweryst,Amand,Amanda",
    "Frumencjusz,Iwona,Sabina,Manfred,Manfreda",
    "Juda,Szymon,Tadeusz,Domabor,Tadea",
    "Euzebia,Franciszek,Longin,Dalia,Ermelinda",
    "Alfons,Alfonsyna,Angel,Edmund,German",
    "Alfons,Alfonsyna,Antoni,Augusta,Godzimir",
    "Andrzej,Konradyn,Konradyna,Jędrzej,Nikola",
    "Ambroży,Bohdana,Bożydar,Agapiusz,Eudoksjusz",
    "Bogumił,Cezary,Chwalisław,German,Hubert",
    "Emeryk,Karol Boromeusz,Mściwój,Agrykola,Dżesika",
    "Blandyn,Blandyna,Dalemir,Florian,Gwidon",
    "Feliks,Leonard,Trzebowit,Daniela,Gabriela",
    "Achilles,Antoni,Engelbert,Amaranta,Florencjusz",
    "Dymitr,Godfryd,Gotfryd,Adrian,Bożydar",
    "Bogudar,Genowefa,Nestor,Joanna,Teodor",
    "Andrzej,Lena,Leon,Jędrzej,Leona",
    "Anastazja,Bartłomiej,Maciej,Jozafat,Marcin",
    "Cibor,Czcibor,Izaak,Arsacjusz,Jonasz",
    "Arkadiusz,Arkady,Brykcjusz,Augustyna,Dalmacjusz",
    "Aga,Agata,Damian,Agryppa,Antyd",
    "Albert,Alberta,Albertyna,Alfons,Artur",
    "Aureliusz,Dionizy,Edmund,Agnieszka,Ariel",
    "Dionizy,Floryn,Grzegorz,Hugo,Jozafat",
    "Aniela,Cieszymysł,Filipina,Gabriela,Galezy",
    "Elżbieta,Mironiega,Paweł,Barbara,Kryspin",
    "Anatol,Edmund,Feliks,Agapiusz,Ampeliusz",
    "Albert,Alberta,Albertyna,Elwira,Heliodor",
    "Cecylia,Marek,Maur,Markusław,Wszemiła",
    "Adela,Erast,Felicyta,Fotyna,Klemens",
    "Dobrosław,Emilia,Emma,Agnieszka,Biruta",
    "Erazm,Jozafat,Katarzyna,Piotr,Tęgomir",
    "Delfin,Dobiemiest,Jan,Konrad,Lechosław",
    "Damazy,Dominik,Leonard,Achacy,Achacjusz",
    "Gościrad,Grzegorz,Jakub,Berta,Ginter",
    "Błażej,Bolemysł,Fryderyk,Klementyna,Paramon",
    "Andrzej,Justyna,Konstanty,Jędrzej,Kutbert",
    "Długosz,Edmund,Eliga,Bianka,Blanka",
    "Adria,Aurelia,Balbina,Bibiana,Budzisław",
    "Franciszek,Kasjan,Ksawery,Atalia,Gerlinda",
    "Barbara,Berno,Biernat,Chrystian,Hieronim",
    "Anastazy,Gerald,Geraldyna,Dalmacjusz,Edyta",
    "Dionizja,Emilian,Jarema,Agata,Angelika",
    "Agaton,Ambroży,Marcin,Józefa,Marcisław",
    "Boguwola,Klement,Maria,Apollo(n),Narcyza",
    "Delfina,Joachim,Joachima,Leokadia,Natasza",
    "Andrzej,Daniel,Judyta,Jędrzej,Brajan",
    "Damazy,Daniela,Julia,Daniel,Stefan",
    "Adelajda,Aleksander,Dagmara,Edburga,Joanna",
    "Lucja,Łucja,Otylia,Aubert,Auksencjusz",
    "Alfred,Arseniusz,Izydor,Heron,Nahum",
    "Celina,Fortunata,Iga,Cecylia,Mścigniew",
    "Adelajda,Ado,Albina,Agrykola,Alina",
    "Florian,Jolanta,Łazarz,Łukasz,Żyrosław",
    "Bogusław,Gracjan,Gracjana,Arkadia,Auksencjusz",
    "Abraham,Beniamin,Dariusz,Bogumiła,Kazimiera",
    "Amon,Bogumiła,Dominik,Dagmara,Liberat",
    "Balbin,Festus,Honorat,Piotr,Temistokles",
    "Beata,Drogomir,Flawian,Franciszka,Gryzelda",
    "Dagobert,Mina,Sławomir,Anatolia,Anatola",
    "Ada,Adam,Adamina,Adela,Druzjanna",
    "Anastazja,Eugenia,Piotr",
    "Dionizy,Szczepan,Wróciwoj,Wrociwoj",
    "Cezary,Fabia,Fabiola,Jan,Krystyna",
    "Antoni,Dobrowiest,Emma,Dobrowieść,Domna",
    "Domawit,Dominik,Gosław,Dawid,Ekard",
    "Dawid,Dawida,Dionizy,Anizja,Egwin",
    "Korneliusz,Mariusz,Melania,Donata,Saturnina",
    "",
]
DAYS_IN_MONTH = [0,31,28,31,30,31,30,31,31,30,31,30,31]

def nameday_index(month, day):
    idx = sum(DAYS_IN_MONTH[m] for m in range(1, month)) + day - 1
    total = sum(DAYS_IN_MONTH)
    return min(idx, total - 1)

def short_date(now):
    return f"{now.day} {MONTH_PL[now.month-1]} {now.year}"

def _nameday_list(now):
    idx = nameday_index(now.month, now.day)
    if 0 <= idx < len(NAMEDAYS):
        names = NAMEDAYS[idx].split(",")
        return names[:5]
    return []

def nameday_text(now):
    names = _nameday_list(now)
    if names:
        return f"Imieniny: {', '.join(names)}"
    return ""

def nameday_names_only(now):
    idx = nameday_index(now.month, now.day)
    if 0 <= idx < len(NAMEDAYS):
        return re.sub(r",(?!\s)", ", ", NAMEDAYS[idx])
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
    sh = hex_char(scroll // 10)
    sl = hex_char(scroll % 10)
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
        return [(msg.get("text", ""), msg.get("font", 1), msg.get("line", 0),
                 msg.get("alignment", 1), msg.get("pos_x", 0),
                 msg.get("width", 96), msg.get("scroll", 99))]

    elif preset == "single-static":
        return [(msg.get("text", ""), msg.get("font", 1), msg.get("line", 0),
                 msg.get("alignment", 0), msg.get("pos_x", 0),
                 msg.get("width", 96), 0)]

    elif preset == "two-static":
        lines = msg.get("text", "").split("||")
        f1 = msg.get("font", 1)
        a1 = msg.get("alignment", 0)
        f2 = msg.get("_ts_font2", 1)
        a2 = msg.get("_ts_align2", 0)
        if len(lines) >= 1 and lines[0].strip():
            parts.append((lines[0].strip(), f1, 0, a1, 0, 96, 0))
        if len(lines) >= 2 and lines[1].strip():
            parts.append((lines[1].strip(), f2, 1, a2, 0, 96, 0))
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
        # Time (font 3, line 0, left) + date (font 1, line 0, right) + weekday (font 1, line 1, under date)
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        time_width = sum(4 if c == '1' else (2 if c == ':' else 6) for c in time_str) + len(time_str) - 1
        shift = msg.get("_clock_shift", 0)
        time_right = max(6, min(60, 2 + time_width + 2 + shift))
        parts.append(("__clock_time__", 3, 0, 0, 2, time_right, 0))
        date_x = time_right + 4
        parts.append(("__clock_date__", 1, 0, 0, date_x, 96, 0))
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

    elif preset == "dht22":
        temp = state.dht22_temp_str
        hum = state.dht22_hum_str
        ok = state.dht22_ok
        parts.append((f"Temp: {temp} st.", 1, 0, 1, 0, 96, 0))
        if ok:
            parts.append((f"Wilg: {hum} pct.", 1, 1, 1, 0, 96, 0))
        else:
            parts.append(("Brak czujnika", 1, 1, 1, 0, 96, 0))
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

def preset_frames(msg):
    """Compute the hex frames for a preset without sending."""
    parts = expand_preset(msg)
    frames = []
    for text, font, line, align, x, w, scroll in parts:
        t = fill_dynamic(text)
        if t == "" and text.startswith("__"):
            t = " "
        frames.append(make_message(t, font, line, align, x, w, scroll))
    return frames

def send_preset(ser, msg, gap_ms=100, frames=None):
    """Send a complete preset (may be multiple display commands) with gaps."""
    if frames is None:
        frames = preset_frames(msg)
    logs = []
    for frame in frames:
        r = send_raw(ser, frame)
        logs.append(r)
        if len(frames) > 1:
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
            "random_mode": False,
        }
        self.override = {"active": False, "message": {}, "expires_at": 0}
        self.queue_pos = 0
        self.queue_thread_running = False
        self.serial = None
        self.dht22_temp_str = "--.-"
        self.dht22_hum_str = "--"
        self.dht22_ok = False

    def next_id(self):
        import uuid
        return str(uuid.uuid4())[:8]

state = State()

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"messages": state.messages}, f, ensure_ascii=False, indent=2)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            state.messages = data.get("messages", [])
            print(f"Loaded {len(state.messages)} messages from {DATA_FILE}")
        except Exception as e:
            print(f"Failed to load {DATA_FILE}: {e}")

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(state.settings, f, ensure_ascii=False, indent=2)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            state.settings.update(saved)
            print(f"Loaded settings from {SETTINGS_FILE}")
        except Exception as e:
            print(f"Failed to load {SETTINGS_FILE}: {e}")

def queue_loop():
    while state.queue_thread_running:
        if state.override.get("active"):
            exp = state.override.get("expires_at", 0)
            if exp and time.time() >= exp:
                state.override = {"active": False, "message": {}, "expires_at": 0}
            else:
                om = state.override.get("message", {})
                if om.get("preset_id") in ("clock", "imieniny"):
                    frames = preset_frames(om)
                    if frames != getattr(state, 'last_frames', None):
                        do_clear = True
                        if om.get("preset_id") == "clock":
                            old = getattr(state, '_clock_time', '')
                            new = fill_dynamic("__clock_time__")
                            if old and new and old[0] == new[0] and len(old) == len(new):
                                do_clear = False
                            state._clock_time = new
                        if do_clear:
                            send_blank(state.serial)
                            time.sleep(0.05)
                        send_preset(state.serial, om, state.settings.get("preset_gap_ms", 100), frames)
                        state.last_frames = frames
            time.sleep(1)
            continue
        if not state.settings["queue_running"]:
            time.sleep(1)
            continue
        now = time.time()
        visible = []
        for m in state.messages:
            if m.get("hidden"):
                continue
            sched = m.get("schedule") or {}
            if sched.get("enabled"):
                if sched.get("from_ts", 0) and now < sched["from_ts"]:
                    continue
                if sched.get("to_ts", 0) and now > sched["to_ts"]:
                    continue
            visible.append(m)
        if not visible:
            time.sleep(1)
            continue
        if state.queue_pos >= len(state.messages):
            state.queue_pos = 0
        msg = state.messages[state.queue_pos]
        if msg.get("hidden"):
            state.queue_pos += 1
            continue
        if now < getattr(state, 'display_until', 0):
            time.sleep(1)
            continue
        frames = preset_frames(msg)
        if frames != getattr(state, 'last_frames', None):
            send_blank(state.serial)
            time.sleep(0.05)
        send_preset(state.serial, msg, state.settings.get("preset_gap_ms", 100), frames)
        state.last_frames = frames
        state.display_until = now + msg.get("duration_sec", 30)
        if state.settings.get("random_mode"):
            import random
            state.queue_pos = state.messages.index(random.choice(visible))
        else:
            state.queue_pos += 1

def arduino_reader(port_path):
    print(f"Arduino reader: connecting to {port_path} ...")
    while state.queue_thread_running:
        try:
            ser = serial.Serial(port_path, 9600, timeout=2)
            print(f"Arduino DHT22 on {port_path}")
            state.dht22_ok = False
            while state.queue_thread_running:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                if line.startswith("T:") and " H:" in line:
                    try:
                        parts = line.split()
                        temp_s = parts[0][2:]
                        hum_s = parts[1][2:]
                        float(temp_s)
                        float(hum_s)
                        state.dht22_temp_str = temp_s
                        state.dht22_hum_str = hum_s
                        if not state.dht22_ok:
                            print(f"DHT22: {temp_s}C {hum_s}%")
                        state.dht22_ok = True
                    except (ValueError, IndexError):
                        pass
                elif line == "ERR":
                    state.dht22_ok = False
        except serial.SerialException as e:
            print(f"Arduino serial error: {e}")
            state.dht22_ok = False
            time.sleep(5)
        except Exception as e:
            print(f"Arduino reader error: {e}")
            state.dht22_ok = False
            time.sleep(5)

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
                "override_message": state.override.get("message", {}),
                "time_synced": getattr(state, '_synced_time', 0) > 0,
                "settings": state.settings,
                "dht22_temp": state.dht22_temp_str,
                "dht22_hum": state.dht22_hum_str,
                "dht22_ok": state.dht22_ok,
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
            save_data()
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
                msg = b["message"]
                frames = preset_frames(msg)
                send_blank(state.serial)
                time.sleep(0.05)
                send_preset(state.serial, msg, state.settings.get("preset_gap_ms", 100), frames)
                state.last_frames = frames
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
            save_data()
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
                    state.queue_pos = i + 1
                    state.display_until = time.time() + m.get("duration_sec", 30)
                    frames = preset_frames(m)
                    send_blank(state.serial)
                    time.sleep(0.05)
                    send_preset(state.serial, m, state.settings.get("preset_gap_ms", 100), frames)
                    state.last_frames = frames
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
                    save_data()
                    return self._json(b)
            self._json({"error": "not found"}, 404)
        elif p == "/api/settings":
            state.settings.update(self._body())
            save_settings()
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
            save_data()
            self._json({"ok": True})
        else:
            self._json({"error": "not found"}, 404)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=8080, type=int)
    ap.add_argument("--serial", default="/dev/cu.usbmodem5A7E0300181")
    ap.add_argument("--arduino-serial", default=None, help="Serial port for DHT22 Arduino")
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

    load_data()
    load_settings()

    state.queue_thread_running = True

    if args.arduino_serial:
        threading.Thread(target=arduino_reader, args=(args.arduino_serial,), daemon=True).start()
    else:
        print("No Arduino sensor (use --arduino-serial /dev/... for DHT22)")

    html = load_html()
    print(f"WebUI loaded ({len(html)} bytes)")

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
        save_data()
        if state.serial:
            state.serial.close()
        srv.server_close()

if __name__ == "__main__":
    main()
