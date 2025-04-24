import google.generativeai as genai
import time
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

genai.configure(api_key="Kod api")

MODEL_NAME = "models/gemini-1.5-pro-latest"

try:
    model = genai.GenerativeModel(MODEL_NAME)
    logger.info(f"Pomyślnie załadowano model {MODEL_NAME}")
except Exception as e:
    logger.error(f"Nie udało się załadować modelu {MODEL_NAME}: {str(e)}")
    raise RuntimeError(f"\u274c Nie udało się załadować modelu {MODEL_NAME}: {e}")

motif_cache = {}
story_cache = {}
chapter_cache = {}

def opisz_motyw(motyw):
    if motyw in motif_cache:
        logger.info(f"Pobrano opis motywu '{motyw}' z pamięci podręcznej")
        return motif_cache[motyw]

    prompt = f"Krótko opisz literacki motyw '{motyw}' w 2-3 zdaniach, w prosty sposób."
    logger.info(f"Generowanie opisu dla motywu: {motyw}")

    try:
        response = model.generate_content(prompt)
        opis = response.text
        motif_cache[motyw] = opis
        time.sleep(2)
        logger.info(f"Pomyślnie wygenerowano opis dla motywu: {motyw}")
        return opis
    except Exception as e:
        logger.error(f"Błąd podczas generowania opisu motywu '{motyw}': {str(e)}")
        return f"Błąd podczas generowania opisu motywu: {str(e)}"

def wygeneruj_historie(motyw, age="16+", hero1_age="25", hero2_age="30", erotic_level=1, setting="Polska", specific_location="", genre="Fantasy", narration="3 osoba", mood="Tajemniczy", main_goal="", focus="Wydarzenia"):
    cache_key = f"{motyw}_{age}_{hero1_age}_{hero2_age}_{erotic_level}_{setting}_{specific_location}_{genre}_{narration}_{mood}_{main_goal}_{focus}"
    if cache_key in story_cache:
        logger.info(f"Pobrano historię z pamięci podręcznej dla klucza: {cache_key}")
        return story_cache[cache_key]

    erotic_descriptions = {
        1: "bez żadnych elementów erotycznych",
        2: "z odrobiną elementów erotycznych (np. subtelne pocałunki, delikatna bliskość)",
        3: "z umiarkowanymi elementami erotycznymi (np. namiętne pocałunki, romantyczne zbliżenia)",
        4: "z wyraźnymi elementami erotycznymi (np. intensywne sceny intymne, opisy fizycznej bliskości)",
        5: "z bardzo intensywnymi elementami erotycznymi (spicy, szczegółowe sceny miłosne)"
    }
    erotic_description = erotic_descriptions.get(erotic_level, "bez żadnych elementów erotycznych")

    # Dodajemy instrukcję, aby upewnić się, że sceny intymne są obecne, jeśli poziom erotyczny > 1
    erotic_instruction = ""
    if erotic_level > 1:
        erotic_instruction = (
            "Historia musi zawierać sceny intymne, takie jak pocałunki, romantyczne zbliżenia lub inne formy fizycznej bliskości między bohaterami, "
            "odpowiednie do wybranego poziomu erotyczności. Skup się na emocjach i chemii między postaciami w tych scenach."
        )

    setting_description = ""
    if specific_location:
        setting_description = f"osadzoną w konkretnym miejscu: {specific_location}, z uwzględnieniem charakterystycznych cech tego miejsca"
    else:
        setting_descriptions = {
            "Polska": "osadzoną w realiach Polski, z uwzględnieniem polskiej kultury, krajobrazów i realiów społecznych",
            "Zagranica": "osadzoną w realiach zagranicznych, w dowolnym kraju poza Polską, z uwzględnieniem tamtejszej kultury i otoczenia",
            "Świat fantasy": "osadzoną w fikcyjnym świecie fantasy, pełnym magii, fantastycznych stworzeń i niezwykłych krain"
        }
        setting_description = setting_descriptions.get(setting, "osadzoną w realiach Polski")

    narration_description = {
        "1 osoba on": "narracja w pierwszej osobie z perspektywy męskiego bohatera",
        "1 osoba ona": "narracja w pierwszej osobie z perspektywy żeńskiego bohatera",
        "3 osoba": "narracja w trzeciej osobie",
        "Rotacyjna": "narracja rotacyjna, przeplatająca perspektywy różnych bohaterów",
        "Dziennik lub list": "narracja w formie dziennika lub listów"
    }.get(narration, "narracja w trzeciej osobie")

    mood_description = f"z dominującym nastrojem: {mood.lower()}"

    focus_description = {
        "Opisy": "skupiającą się na szczegółowych opisach otoczenia i świata",
        "Dialogi": "skupiającą się na dialogach między bohaterami",
        "Wydarzenia": "skupiającą się na dynamicznych wydarzeniach i akcji",
        "Emocje": "skupiającą się na emocjach i wewnętrznych przeżyciach bohaterów",
        "Relacje": "skupiającą się na relacjach i interakcjach między bohaterami"
    }.get(focus, "skupiającą się na dynamicznych wydarzeniach i akcji")

    main_goal_description = f" z głównym celem: {main_goal}" if main_goal else ""

    prompt = (
        f"Stwórz historię literacką opartą na motywie '{motyw}' dla grupy wiekowej {age}, {erotic_description}, {setting_description}, w gatunku {genre.lower()}, "
        f"{narration_description}, {mood_description}, {focus_description}{main_goal_description}. {erotic_instruction} "
        f"Pierwszy bohater ma {hero1_age} lat, a drugi {hero2_age} lat. "
        f"1. Wygeneruj chwytliwy tytuł historii, który pasuje do motywów i klimatu opowieści. "
        f"2. Opis fabuły powinien być krótki, zawierać 4-5 zdań, z uwzględnieniem zawiązania akcji, konfliktu i emocji bohaterów. "
        f"3. Opisz dwóch głównych bohaterów (imię, wiek, szczegółowy opis: wygląd, osobowość, motywacje, tło fabularne). "
        f"4. Opis świata powinien być bardziej szczegółowy, zawierać 2-3 zdania, opisujące miejsce akcji, atmosferę i kluczowe elementy otoczenia. "
        f"Zwróć odpowiedź w formacie:\nTytuł: [tytuł]\nOpis: [opis fabuły]\nBohater 1: [opis pierwszej postaci]\nBohater 2: [opis drugiej postaci]\nŚwiat: [opis świata]"
    )

    logger.info(f"Generowanie historii z promptem: {prompt[:100]}...")

    try:
        response = model.generate_content(prompt)
        result_text = response.text
        time.sleep(2)
        logger.info("Pomyślnie wygenerowano historię")

        lines = result_text.split('\n')
        title = ''
        story = result_text
        for line in lines:
            if line.startswith('Tytuł:'):
                title = line.replace('Tytuł:', '').strip()
                story = '\n'.join([l for l in lines if not l.startswith('Tytuł:')])
                break

        result = {
            'title': title,
            'story': story,
            'motifs': motyw,
            'age': age,
            'hero1_age': hero1_age,
            'hero2_age': hero2_age,
            'erotic_level': erotic_level,
            'setting': setting,
            'specific_location': specific_location,
            'genre': genre,
            'narration': narration,
            'mood': mood,
            'main_goal': main_goal,
            'focus': focus
        }
        story_cache[cache_key] = result
        return result
    except Exception as e:
        logger.error(f"Błąd podczas generowania historii: {str(e)}")
        return f"Błąd podczas generowania historii: {str(e)}"

def wygeneruj_rozdzial(motyw, age="16+", hero1_age="25", hero2_age="30", erotic_level=1, setting="Polska", specific_location="", genre="Fantasy", narration="3 osoba", mood="Tajemniczy", main_goal="", focus="Wydarzenia", chapter_pages=1, previous_content=None):
    cache_key = f"chapter_{motyw}_{age}_{hero1_age}_{hero2_age}_{erotic_level}_{setting}_{specific_location}_{genre}_{narration}_{mood}_{main_goal}_{focus}_{chapter_pages}"
    if cache_key in chapter_cache:
        logger.info(f"Pobrano rozdział z pamięci podręcznej dla klucza: {cache_key}")
        return chapter_cache[cache_key]

    erotic_descriptions = {
        1: "bez żadnych elementów erotycznych",
        2: "z odrobiną elementów erotycznych (np. subtelne pocałunki, delikatna bliskość)",
        3: "z umiarkowanymi elementami erotycznymi (np. namiętne pocałunki, romantyczne zbliżenia)",
        4: "z wyraźnymi elementami erotycznymi (np. intensywne sceny intymne, opisy fizycznej bliskości)",
        5: "z bardzo intensywnymi elementami erotycznymi (spicy, szczegółowe sceny miłosne)"
    }
    erotic_description = erotic_descriptions.get(erotic_level, "bez żadnych elementów erotycznych")

    # Instrukcja dla scen intymnych, jeśli poziom erotyczny > 1
    erotic_instruction = ""
    if erotic_level > 1:
        erotic_instruction = (
            "Rozdział musi zawierać sceny intymne, takie jak pocałunki, romantyczne zbliżenia lub inne formy fizycznej bliskości między bohaterami, "
            "odpowiednie do wybranego poziomu erotyczności. Skup się na emocjach i chemii między postaciami w tych scenach."
        )

    setting_description = ""
    if specific_location:
        setting_description = f"osadzoną w konkretnym miejscu: {specific_location}, z uwzględnieniem charakterystycznych cech tego miejsca"
    else:
        setting_descriptions = {
            "Polska": "osadzoną w realiach Polski, z uwzględnieniem polskiej kultury, krajobrazów i realiów społecznych",
            "Zagranica": "osadzoną w realiach zagranicznych, w dowolnym kraju poza Polską, z uwzględnieniem tamtejszej kultury i otoczenia",
            "Świat fantasy": "osadzoną w fikcyjnym świecie fantasy, pełnym magii, fantastycznych stworzeń i niezwykłych krain"
        }
        setting_description = setting_descriptions.get(setting, "osadzoną w realiach Polski")

    narration_description = {
        "1 osoba on": "narracja w pierwszej osobie z perspektywy męskiego bohatera",
        "1 osoba ona": "narracja w pierwszej osobie z perspektywy żeńskiego bohatera",
        "3 osoba": "narracja w trzeciej osobie",
        "Rotacyjna": "narracja rotacyjna, przeplatająca perspektywy różnych bohaterów",
        "Dziennik lub list": "narracja w formie dziennika lub listów"
    }.get(narration, "narracja w trzeciej osobie")

    mood_description = f"z dominującym nastrojem: {mood.lower()}"

    focus_description = {
        "Opisy": "skupiającą się na szczegółowych opisach otoczenia i świata",
        "Dialogi": "skupiającą się na dialogach między bohaterami",
        "Wydarzenia": "skupiającą się na dynamicznych wydarzeniach i akcji",
        "Emocje": "skupiającą się na emocjach i wewnętrznych przeżyciach bohaterów",
        "Relacje": "skupiającą się na relacjach i interakcjach między bohaterami"
    }.get(focus, "skupiającą się na dynamicznych wydarzeniach i akcji")

    chapter_instruction = f"Rozdział ma mieć około {chapter_pages} stron i być szczegółowy, z rozwinięciem akcji, dialogami i opisami."

    main_goal_description = f" z głównym celem: {main_goal}" if main_goal else ""

    prompt = (
        f"Kontynuuj historię literacką opartą na motywie '{motyw}' dla grupy wiekowej {age}, {erotic_description}, {setting_description}, w gatunku {genre.lower()}, "
        f"{narration_description}, {mood_description}, {focus_description}{main_goal_description}. {erotic_instruction} {chapter_instruction} "
        f"Pierwszy bohater ma {hero1_age} lat, a drugi {hero2_age} lat. "
        f"\n\nOto poprzednia treść historii, którą należy kontynuować w kolejnym rozdziale:\n{previous_content}\n\n"
        f"Kontynuuj historię w sposób spójny, rozwijając fabułę i postacie, zachowując styl i nastrój poprzednich części. "
        f"Zwróć odpowiedź w formacie:\nTytuł: [tytuł]\nRozdział: [treść rozdziału]"
    )

    logger.info(f"Generowanie rozdziału z promptem: {prompt[:100]}...")

    try:
        response = model.generate_content(prompt)
        result_text = response.text
        time.sleep(2)
        logger.info("Pomyślnie wygenerowano rozdział")

        lines = result_text.split('\n')
        title = ''
        story = result_text
        for line in lines:
            if line.startswith('Tytuł:'):
                title = line.replace('Tytuł:', '').strip()
                story = '\n'.join([l for l in lines if not l.startswith('Tytuł:')])
                break

        result = {
            'title': title,
            'story': story,
            'motifs': motyw,
            'age': age,
            'hero1_age': hero1_age,
            'hero2_age': hero2_age,
            'erotic_level': erotic_level,
            'setting': setting,
            'specific_location': specific_location,
            'genre': genre,
            'narration': narration,
            'mood': mood,
            'main_goal': main_goal,
            'focus': focus
        }
        chapter_cache[cache_key] = result
        return result
    except Exception as e:
        logger.error(f"Błąd podczas generowania rozdziału: {str(e)}")
        return f"Błąd podczas generowania rozdziału: {str(e)}"

def znajdz_najbardziej_podobne_tytuly(fragment, lista_tytulow, top_k=5):
    prompt = (
        f"Użytkownik wpisał: '{fragment}'. "
        f"Oto lista tytułów książek:\n" +
        "\n".join(f"- {tytul}" for tytul in lista_tytulow) +
        f"\n\nZwróć maksymalnie {top_k} najbardziej pasujących tytułów. "
        f"Uwzględnij możliwe literówki, skróty, popularne skojarzenia. "
        f"Odpowiedz jako lista tytułów, bez dodatkowego tekstu."
    )
    logger.info(f"Wyszukiwanie podobnych tytułów dla fragmentu: {fragment}")

    try:
        response = model.generate_content(prompt)
        wynik = response.text.strip().split('\n')
        wynik = [w.strip("- ").strip() for w in wynik if w.strip()]
        logger.info(f"Znaleziono pasujące tytuły: {wynik}")
        return wynik
    except Exception as e:
        logger.error(f"Błąd podczas wyszukiwania podobnych tytułów: {str(e)}")
        return []