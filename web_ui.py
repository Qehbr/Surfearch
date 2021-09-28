from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from indexer import Searcher

app = Flask(__name__)
Bootstrap(app)
searcher = Searcher("indexes")


class SearchForm(Form):
    user_query = StringField('user_query', validators=[DataRequired()])
    search_button = SubmitField("Search!")


@app.route("/", methods=["GET", "POST"])
def index():
    search_form = SearchForm(csrf_enabled=False)
    if search_form.validate_on_submit():
        return redirect(url_for("search_results", query=search_form.user_query.data))
    return render_template("index.html", form=search_form)


@app.route("/search_results/<query>")
def search_results(query):
    query_words = query.split(" ")
    docids = searcher.find_documents_AND(query_words)
    urls = [searcher.get_url(docid) for docid in docids]
    texts = [" ".join(searcher.generate_snippet(query_words, docid)) for docid in docids]
    urls_and_texts = zip(urls, texts)
    return render_template("search_results.html", query=query, urls_and_texts=urls_and_texts)


if __name__ == "__main__":
    app.run()
