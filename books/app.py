import json
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from flask import Flask, request, jsonify, render_template

try:
    import anthropic as _anthropic
    _anthropic_client = _anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var
except Exception:
    _anthropic_client = None

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'books.json')


def load_books():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_books(books):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)


def next_id(books):
    if not books:
        return 1
    return max(b['id'] for b in books) + 1


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/books', methods=['GET'])
def list_books():
    books = load_books()
    q = request.args.get('q', '').lower()
    tag = request.args.get('tag', '')
    if q:
        books = [
            b for b in books
            if q in b.get('title', '').lower()
            or q in b.get('author', '').lower()
            or q in b.get('isbn', '').lower()
        ]
    if tag:
        books = [b for b in books if tag in b.get('tags', [])]
    return jsonify(books)


@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.json
    books = load_books()
    isbn = data.get('isbn', '')
    if isbn and any(b.get('isbn') == isbn for b in books):
        return jsonify({'error': 'ISBN already exists'}), 409
    book = {
        'id': next_id(books),
        'title': data['title'],
        'author': data.get('author', ''),
        'isbn': isbn,
        'tags': data.get('tags', []),
        'read_date': data.get('read_date', ''),
        'cover_url': data.get('cover_url', ''),
        'created_at': datetime.now().isoformat(timespec='seconds'),
    }
    books.append(book)
    save_books(books)
    return jsonify(book), 201


@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    books = load_books()
    book = next((b for b in books if b['id'] == book_id), None)
    if book is None:
        return jsonify({'error': 'not found'}), 404
    return jsonify(book)


@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.json
    books = load_books()
    idx = next((i for i, b in enumerate(books) if b['id'] == book_id), None)
    if idx is None:
        return jsonify({'error': 'not found'}), 404
    books[idx].update({
        'title': data['title'],
        'author': data.get('author', ''),
        'isbn': data.get('isbn', ''),
        'tags': data.get('tags', []),
        'read_date': data.get('read_date', ''),
        'cover_url': data.get('cover_url', ''),
    })
    save_books(books)
    return jsonify(books[idx])


@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    books = load_books()
    books = [b for b in books if b['id'] != book_id]
    save_books(books)
    return jsonify({'status': 'ok'})


@app.route('/api/lookup/<isbn>')
def lookup_isbn(isbn):
    # ISBNのハイフンを除去して正規化
    isbn = isbn.replace('-', '').replace(' ', '')

    # 1. 国立国会図書館 API（日本語書籍の網羅性が最高）
    try:
        url = f'https://iss.ndl.go.jp/api/opensearch?isbn={isbn}'
        r = requests.get(url, timeout=5)
        ns = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'rss': 'http://purl.org/rss/1.0/',
        }
        root = ET.fromstring(r.text)
        item = root.find('./channel/item')
        if item is not None:
            title = item.findtext('title') or ''
            author = item.findtext('dc:creator', namespaces=ns) or ''
            # NDL表紙画像（ISBN13で取得）
            isbn13 = isbn if len(isbn) == 13 else ''
            cover_url = f'https://ndlsearch.ndl.go.jp/thumbnail/{isbn13}.jpg' if isbn13 else ''
            return jsonify({'title': title, 'author': author, 'cover_url': cover_url})
    except Exception:
        pass

    # 2. Google Books API
    try:
        url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
        r = requests.get(url, timeout=5)
        data = r.json()
        items = data.get('items', [])
        if items:
            info = items[0]['volumeInfo']
            thumbnail = info.get('imageLinks', {}).get('thumbnail', '')
            if thumbnail.startswith('http://'):
                thumbnail = 'https://' + thumbnail[7:]
            return jsonify({
                'title': info.get('title', ''),
                'author': ', '.join(info.get('authors', [])),
                'cover_url': thumbnail,
            })
    except Exception:
        pass

    # 3. Open Library（洋書向け）
    try:
        url = f'https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data'
        r = requests.get(url, timeout=5)
        data = r.json()
        key = f'ISBN:{isbn}'
        if key in data:
            book = data[key]
            return jsonify({
                'title': book.get('title', ''),
                'author': ', '.join(a['name'] for a in book.get('authors', [])),
                'cover_url': book.get('cover', {}).get('medium', ''),
            })
    except Exception:
        pass

    # 4. Claude API フォールバック（学習データから書誌情報を推定）
    if _anthropic_client:
        try:
            prompt = (
                f'ISBN {isbn} の本について、タイトルと著者名を教えてください。'
                '必ず以下のJSON形式だけで返してください。情報が不明な場合は空文字にしてください。\n'
                '{"title": "...", "author": "..."}'
            )
            msg = _anthropic_client.messages.create(
                model='claude-haiku-4-5',
                max_tokens=256,
                messages=[{'role': 'user', 'content': prompt}],
            )
            text = msg.content[0].text.strip()
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                if data.get('title'):
                    return jsonify({
                        'title': data.get('title', ''),
                        'author': data.get('author', ''),
                        'cover_url': '',
                        'source': 'ai',
                    })
        except Exception:
            pass

    return jsonify({'error': 'not found'}), 404


if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        save_books([])
    app.run(debug=True, port=5001)
