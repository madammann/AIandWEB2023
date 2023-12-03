from flask import Flask, render_template, request

from index import WhooshCustomizedIndex

#we initialize flask app and index
app = Flask(__name__)
index = WhooshCustomizedIndex()

#we provide the logo and background paths from the static folder
BACKGROUND = 'static/background.jpg'
LOGO = 'static/logo.jpg'

#mainpage route returns a html page designed as main page
@app.route("/")
def search_mainpage():
    return render_template("searchpage_main.html", background_path=BACKGROUND, logo_path=LOGO)

#search route with dynamic url returns a page with the search results and the same search bar
@app.route("/search")
def search_results():
    query = " ".join(request.args['q'].split('+'))
    urls, titles, texts = index.search(query)

    return render_template("searchpage_results.html", urls=urls, titles=titles, texts=texts, q=query, zip=zip, background_path=BACKGROUND, logo_path=LOGO)

if __name__ == "__main__":
    app.run()