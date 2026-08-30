from flask import Flask, jsonify

app = Flask(__name__)
BOOKS = {1: {"id": 1, "title": "The Left Hand of Darkness"}, 2: {"id": 2, "title": "Kindred"}}


@app.get("/books/<int:book_id>")
def get_book(book_id: int):
    book = BOOKS.get(book_id)
    return jsonify({"book": book})
