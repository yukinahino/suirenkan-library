import json
from urllib.parse import urlencode
from urllib.request import urlopen


title = "おおきな木"

base_url = "https://www.googleapis.com/books/v1/volumes"

params = {
    "q": f'intitle:"{title}"',
    "maxResults": 5,
    "langRestrict": "ja"
}

url = base_url + "?" + urlencode(params)


print("Google Books APIに接続します...")
print(url)


try:

    # timeoutを10秒に設定
    with urlopen(url, timeout=10) as response:

        print("Google Books APIから応答がありました。")

        data = json.loads(
            response.read().decode("utf-8")
        )


    items = data.get("items", [])

    print(f"\n検索結果：{len(items)}件")
    print("-" * 50)


    for i, item in enumerate(items, start=1):

        info = item.get("volumeInfo", {})

        book_title = info.get("title")
        authors = info.get("authors", [])
        publisher = info.get("publisher")
        identifiers = info.get("industryIdentifiers", [])
        image_links = info.get("imageLinks", {})

        isbn13 = None

        for identifier in identifiers:

            if identifier.get("type") == "ISBN_13":

                isbn13 = identifier.get("identifier")
                break


        cover_image = image_links.get("thumbnail")


        print(f"【候補 {i}】")
        print(f"タイトル：{book_title}")
        print(f"著者：{', '.join(authors)}")
        print(f"出版社：{publisher}")
        print(f"ISBN-13：{isbn13}")
        print(f"書影：{cover_image}")
        print("-" * 50)


except Exception as error:

    print("\nエラーが発生しました。")
    print(type(error).__name__)
    print(error)