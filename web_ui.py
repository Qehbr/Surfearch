from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, abort
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from indexer import ShelveIndexes
from searcher import Searcher, generate_snippet
from lang_proc import to_query_terms

app = Flask(__name__)
Bootstrap(app)
searcher = Searcher("indexes", ShelveIndexes)


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page


class SearchForm(Form):
    user_query = StringField('Query', validators=[DataRequired()])
    search_button = SubmitField("Search!")


@app.route("/", methods=["GET", "POST"])
def index():
    search_form = SearchForm(csrf_enabled=False)
    if search_form.validate_on_submit():
        return redirect(url_for("search_results", query=search_form.user_query.data))
    return render_template("index.html", form=search_form)


@app.route("/search_results/<query>", defaults={'page': 1})
@app.route("/search_results/<query>/<int:page>")
def search_results(query, page):
    start_time = datetime.now()
    query_terms = to_query_terms(query)
    page_size = 25
    search_result = searcher.find_documents_and_rank_by_bm25(query_terms)
    docs = search_result.get_page(page, page_size)
    pagination = search_result.get_pagination(page, page_size)
    if page > pagination.pages:
        abort(404)
    texts = []
    urls = []
    titles = []
    for docid in docs:
        title = searcher.indexes.get_title(docid)
        text = searcher.indexes.get_document_text(docid)
        url = searcher.indexes.get_url(docid)

        titles.append(title)
        texts.append(generate_snippet(query_terms, text))
        urls.append(url)

    titles_texts_and_urls = zip(titles, texts, urls)

    finish_time = datetime.now()

    return render_template("search_results.html",
                           processing_time=(finish_time - start_time),
                           offset=((page - 1) * page_size),
                           total_doc_num=search_result.total_doc_num(),
                           pagination=pagination,
                           query=query,
                           titles_texts_and_urls=titles_texts_and_urls)


if __name__ == "__main__":
    app.run()
