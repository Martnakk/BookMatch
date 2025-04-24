from flask import Flask, request, jsonify, render_template, make_response
import pandas as pd
import random
import time
import json
from datetime import datetime
from gemini_ai import opisz_motyw, znajdz_najbardziej_podobne_tytuly, wygeneruj_historie, wygeneruj_rozdzial

# Wczytaj dane z pliku Excel
df = pd.read_excel("baza 1.xlsx")
df.columns = [col.strip().lower() for col in df.columns]

# Kolumny
title_col = 'tytuł'
motif_col = 'motywy'
author_col = 'autor'
age_col = 'wiek'
publisher_col = 'wydawnictwo'

# Plik do przechowywania archiwum
ARCHIVE_FILE = "story_archive.json"

# Funkcja do wczytywania archiwum
def load_archive():
    try:
        with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Funkcja do zapisywania archiwum
def save_to_archive(title, story, is_chapter=False, parent_title=None):
    archive = load_archive()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = {
        'title': title,
        'story': story,
        'timestamp': timestamp,
        'is_chapter': is_chapter,
        'parent_title': parent_title
    }
    archive.append(entry)
    with open(ARCHIVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(archive, f, ensure_ascii=False, indent=4)

# Konwersja DataFrame na JSON dla pamięci przeglądarki
initial_data = df.to_dict(orient='records')
for record in initial_data:
    record[motif_col] = str(record[motif_col])

app = Flask(__name__)

# Funkcja do ładowania danych z cookies
def load_data_from_storage():
    global df
    stored_data = request.cookies.get('book_data')
    if stored_data:
        stored_df = pd.DataFrame(json.loads(stored_data))
        stored_df.columns = [col.strip().lower() for col in stored_df.columns]
        df = stored_df
    else:
        df = pd.read_excel("baza 1.xlsx")
        df.columns = [col.strip().lower() for col in df.columns]

@app.route('/')
def index():
    load_data_from_storage()
    response = make_response(render_template('index.html'))
    response.set_cookie('book_data', json.dumps(df.to_dict(orient='records')))
    return response

@app.route('/create_story.html')
def create_story():
    load_data_from_storage()
    response = make_response(render_template('create_story.html'))
    response.set_cookie('book_data', json.dumps(df.to_dict(orient='records')))
    return response

@app.route('/index.html')
def index_html():
    load_data_from_storage()
    response = make_response(render_template('index.html'))
    response.set_cookie('book_data', json.dumps(df.to_dict(orient='records')))
    return response

@app.route('/get_archive', methods=['GET'])
def get_archive():
    load_data_from_storage()
    archive = load_archive()
    response = make_response(jsonify({'archive': archive}))
    response.set_cookie('book_data', json.dumps(df.to_dict(orient='records')))
    return response

@app.route('/search_books', methods=['POST'])
def search_books():
    load_data_from_storage()
    data = request.get_json()
    fragment_tytulu = data.get('fragment_tytulu')

    if not fragment_tytulu:
        return jsonify({'error': 'Proszę podać fragment tytułu książki.'}), 400

    wszystkie_tytuly = df[title_col].tolist()
    start_time = time.time()
    trafione_tytuly = znajdz_najbardziej_podobne_tytuly(fragment_tytulu, wszystkie_tytuly)
    end_time = time.time()
    print(f"Wyszukiwanie podobnych tytułów dla '{fragment_tytulu}' zajęło {end_time - start_time:.2f} sekund")

    pasujace = df[df[title_col].isin(trafione_tytuly)]

    if pasujace.empty:
        return jsonify({'error': 'Nie znaleziono żadnej książki z takim tytułem.'}), 404

    books = []
    for i, row in pasujace.iterrows():
        books.append({
            'index': i,
            'title': row[title_col],
            'author': row[author_col],
            'publisher': row[publisher_col],
            'age': row[age_col],
            'motifs': [m.strip() for m in str(row[motif_col]).split(",")]
        })

    response = make_response(jsonify({'books': books}))
    response.set_cookie('book_data', json.dumps(df.to_dict(orient='records')))
    return response

@app.route('/select_book', methods=['POST'])
def select_book():
    load_data_from_storage()
    data = request.get_json()
    book_index = data.get('book_index')
    motif_index = data.get('motif_index', None)

    if book_index is None:
        return jsonify({'error': 'Proszę wybrać książkę.'}), 400

    try:
        wybrana = df.loc[int(book_index)]
    except (KeyError, ValueError):
        return jsonify({'error': 'Nieprawidłowy indeks książki.'}), 400

    motywy = [m.strip() for m in str(wybrana[motif_col]).split(",")]

    if motif_index is None:
        return jsonify({
            'motifs': motywy
        })

    try:
        wybrany_motyw = motywy[int(motif_index)]
    except (IndexError, ValueError):
        return jsonify({'error': 'Nieprawidłowy indeks motywu.'}), 400

    start_time = time.time()
    opis = opisz_motyw(wybrany_motyw)
    end_time = time.time()
    print(f"Generowanie opisu motywu '{wybrany_motyw}' zajęło {end_time - start_time:.2f} sekund")

    fragment_tytulu = wybrana[title_col].lower()
    wybrany_autor = wybrana[author_col].lower()
    
    import re
    rdzen_tytulu = re.sub(r'\s*[IVXLCDM]+|\s*\d+|\s*(tom|część+)\s*\d+', '', fragment_tytulu).strip()

    podobne = df[
        (~df[title_col].str.lower().str.contains(fragment_tytulu, na=False)) &
        (df[motif_col].str.lower().str.contains(wybrany_motyw.lower(), na=False)) &
        (~df[author_col].str.lower().str.contains(wybrany_autor, na=False)) &
        (~df[title_col].str.lower().str.contains(rdzen_tytulu, na=False))
    ]

    similar_books = []
    if not podobne.empty:
        liczba_do_wyswietlenia = min(3, len(podobne))
        losowe = podobne.sample(n=liczba_do_wyswietlenia, random_state=random.randint(1, 9999))
        for _, ksiazka in losowe.iterrows():
            similar_books.append({
                'index': int(ksiazka.name),
                'title': str(ksiazka[title_col]),
                'author': str(ksiazka[author_col]),
                'age': str(ksiazka[age_col]),
                'publisher': str(ksiazka[publisher_col])
            })

    response = make_response(jsonify({
        'selected_motif': wybrany_motyw,
        'motif_description': opis,
        'similar_books': similar_books
    }))
    response.set_cookie('book_data', json.dumps(df.to_dict(orient='records')))
    return response

# Przechowywanie historii w pamięci podręcznej
story_cache = {}

@app.route('/generate_custom_story', methods=['POST'])
def generate_custom_story():
    load_data_from_storage()
    data = request.get_json()
    age = data.get('age')
    hero1_age = data.get('hero1_age')
    hero2_age = data.get('hero2_age')
    erotic_level = data.get('erotic_level', 1)
    setting = data.get('setting', 'Polska')
    specific_location = data.get('specific_location', '')
    genre = data.get('genre', 'Fantasy')
    narration = data.get('narration', '3 osoba')
    mood = data.get('mood', 'Tajemniczy')
    main_goal = data.get('main_goal', '')
    focus = data.get('focus', 'Wydarzenia')
    motifs = data.get('motifs', [])

    if not age:
        return jsonify({'error': 'Proszę podać wiek odbiorców.'}), 400

    if not hero1_age or not hero2_age:
        return jsonify({'error': 'Proszę podać wiek obu bohaterów.'}), 400

    if not motifs or len(motifs) < 3:
        return jsonify({'error': 'Proszę podać minimum 3 motywy.'}), 400

    motifs_str = ", ".join(motifs)
    start_time = time.time()
    try:
        result = wygeneruj_historie(
            motifs_str, 
            age=age, 
            hero1_age=hero1_age, 
            hero2_age=hero2_age, 
            erotic_level=erotic_level, 
            setting=setting, 
            specific_location=specific_location, 
            genre=genre, 
            narration=narration, 
            mood=mood, 
            main_goal=main_goal, 
            focus=focus
        )
    except Exception as e:
        print(f"Błąd podczas generowania historii: {str(e)}")
        return jsonify({'error': f'Błąd podczas generowania historii: {str(e)}'}), 500

    end_time = time.time()
    print(f"Generowanie historii dla motywów '{motifs_str}' zajęło {end_time - start_time:.2f} sekund")

    if isinstance(result, dict):
        story_id = str(random.randint(100000, 999999))
        story_cache[story_id] = result
        save_to_archive(result['title'], result['story'], is_chapter=False, parent_title=None)
        response = make_response(jsonify({
            'story_id': story_id,
            'title': result['title'],
            'story': result['story']
        }))
    else:
        response = make_response(jsonify({'error': result}), 500)

    response.set_cookie('book_data', json.dumps(df.to_dict(orient='records')))
    return response

@app.route('/generate_chapter', methods=['POST'])
def generate_chapter():
    load_data_from_storage()
    data = request.get_json()
    story_id = data.get('story_id')
    chapter_pages = int(data.get('chapter_pages', 1))
    parent_title = data.get('parent_title', '')

    if not story_id or story_id not in story_cache:
        return jsonify({'error': 'Nieprawidłowy identyfikator historii.'}), 400

    previous_story = story_cache[story_id]
    start_time = time.time()
    try:
        result = wygeneruj_rozdzial(
            previous_story['motifs'], 
            age=previous_story['age'], 
            hero1_age=previous_story['hero1_age'], 
            hero2_age=previous_story['hero2_age'], 
            erotic_level=previous_story['erotic_level'], 
            setting=previous_story['setting'], 
            specific_location=previous_story['specific_location'], 
            genre=previous_story['genre'], 
            narration=previous_story['narration'], 
            mood=previous_story['mood'], 
            main_goal=previous_story['main_goal'], 
            focus=previous_story['focus'], 
            chapter_pages=chapter_pages, 
            previous_content=previous_story['story']
        )
    except Exception as e:
        print(f"Błąd podczas generowania rozdziału: {str(e)}")
        return jsonify({'error': f'Błąd podczas generowania rozdziału: {str(e)}'}), 500

    end_time = time.time()
    print(f"Generowanie rozdziału zajęło {end_time - start_time:.2f} sekund")

    if isinstance(result, dict):
        story_cache[story_id] = result
        save_to_archive(result['title'], result['story'], is_chapter=True, parent_title=parent_title)
        response = make_response(jsonify({
            'title': result['title'],
            'story': result['story']
        }))
    else:
        response = make_response(jsonify({'error': result}), 500)

    response.set_cookie('book_data', json.dumps(df.to_dict(orient='records')))
    return response

@app.route('/add_book', methods=['POST'])
def add_book():
    global df
    load_data_from_storage()
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    age = data.get('age')
    publisher = data.get('publisher')
    motifs = data.get('motifs')

    if not all([title, author, age, publisher, motifs]):
        return jsonify({'error': 'Proszę wypełnić wszystkie pola.'}), 400

    new_book = {
        title_col: title,
        author_col: author,
        age_col: age,
        publisher_col: publisher,
        motif_col: motifs
    }

    df = pd.concat([df, pd.DataFrame([new_book])], ignore_index=True)

    try:
        df.to_excel("baza 1.xlsx", index=False)
    except Exception as e:
        print(f"Błąd podczas zapisywania książki do pliku Excel: {str(e)}")

    books = []
    for i, row in df.iterrows():
        books.append({
            'index': i,
            'title': row[title_col],
            'author': row[author_col],
            'publisher': row[publisher_col],
            'age': row[age_col],
            'motifs': [m.strip() for m in str(row[motif_col]).split(",")]
        })

    response = make_response(jsonify({'message': 'Książka została dodana!', 'books': books}))
    response.set_cookie('book_data', json.dumps(df.to_dict(orient='records')))
    return response

if __name__ == '__main__':
    print("Uruchamianie aplikacji Flask...")
    app.run(debug=True, host='127.0.0.1', port=5000)
    print("Aplikacja działa na: http://127.0.0.1:5000")