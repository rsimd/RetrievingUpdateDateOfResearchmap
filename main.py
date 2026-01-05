"""
## Researchmap checker (修正版 2026/01/05）
```
__author__ = "Riki Murakami"
__license__ = "MIT"
__version__ = "1.0.2"
__maintainer__ = "Riki Murakami"
__email__ = "mriki@ichinoseki.ac.jp"
__status__ = "Production"
```


requestsでhtmlをdlできなくなっていたが，APIは機関のAPI Keyがないと使えないらしい[要出展]ので，seleniumで強引にスクレイピングを行う．これはバックグラウンドで実際にchromeを起動しているため，htmlのDLに時間がかかる．また，デフォルトインターバルでは取得がうまくいかない（e.g. 論文が多すぎてページが重い）場合，更新日の取得時にエラーを発するので，例外処理中で再度その研究者ページのHTMLをDLする．  
そのため非常に遅い（e.g. $ 60\text{[人]} \times 10 \text{[sec]}=600\text{[sec]}$）ので，時間に余裕を持って実行すること．

また，もしもcolabで実行する場合は以下のプログラムをコードセルへコピーして実行してから，Pythonスクリプトを実行すること．

```sh
%%shell

# 更新を実行
sudo apt -y update

# ダウンロードのために必要なパッケージをインストール
sudo apt install -y wget curl unzip
# 以下はChromeの依存パッケージ
wget http://archive.ubuntu.com/ubuntu/pool/main/libu/libu2f-host/libu2f-udev_1.1.4-1_all.deb
dpkg -i libu2f-udev_1.1.4-1_all.deb

# Chromeのインストール
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i google-chrome-stable_current_amd64.deb

# Chrome Driverのインストール
CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`
wget -N https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip -P /tmp/
unzip -o /tmp/chromedriver_linux64.zip -d /tmp/
chmod +x /tmp/chromedriver
mv /tmp/chromedriver /usr/local/bin/chromedriver
```
インストールスクリプトの出典： [Google ColaboratoryでSeleniumを使うための設定方法 | DevelopersIO](https://dev.classmethod.jp/articles/google-colaboratory-use-selenium/)

"""


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime 
from tqdm import tqdm, trange
import argparse
from pathlib import Path

def get_pages(url, interval=5):
    # Chromeのオプションを設定
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # ヘッドレスモードで実行
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Chromeドライバのパスを設定
    service = Service(ChromeDriverManager().install())
    
    # ブラウザを起動
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # URLにアクセス
    driver.get(url)
    page_source = driver.page_source
    time.sleep(interval)
    driver.quit()
    return page_source

def get_researchers(page_src:str)->pd.DataFrame:
    soup = BeautifulSoup(page_src, "html.parser")
    kana_list = []
    name_list = []
    url_list = []
    pipeline = [
        soup.find_all("div", {"class": "rm-cv-card-kana"}),
        soup.find_all("div", {"class": "rm-cv-card-name"}),
        ]

    for (div_kana,div_name,) in zip(*pipeline):
        kana = div_kana.text.strip()
        kana_list.append(kana)
        name = div_name.text.strip()
        name_list.append(name)
        url = div_name.find("a")["href"]
        url = "https://researchmap.jp/"+url
        url_list.append(url)

    df = pd.DataFrame(name_list, columns=["name"])
    df["kana"] = kana_list
    df["url"] = url_list
    return df

def get_update_date(page_src:str)->str:
    soup = BeautifulSoup(page_src, "html.parser")
    elements = soup.find_all("div", attrs={"class":"rm-modified text-right"})
    if not elements:
        # 要素が見つからない場合は空の文字列を返す．
        return ""
    element = elements[0]
    date = element.text.strip().replace("更新日: ","")
    if len(date.split("/")) == 2:
        date = f"{datetime.today().year}/{date}"
    return date

def parse_args():
    parser = argparse.ArgumentParser(description="Researchmapの更新日を取得するプログラム")
    parser.add_argument("--institution_code", type=str, default="6520", help="institution code. 学校ごとに違います．")
    parser.add_argument("--limit", type=int, default=200, help="limit. 研究者数がlimitを超えた場合はlimitを超えた分は取得できないので，多めに指定してください．")
    return parser.parse_args()

if __name__ == "__main__":
    ## Researchmapからhtml収集
    args = parse_args()
    url = f"https://researchmap.jp/researchers?institution_code={args.institution_code}&limit={args.limit}"
    page_source = get_pages(url)
    df = get_researchers(page_source)
    tmp = []
    for url,name in tqdm(zip(df.url, df.name),total=df.shape[0]):
        time.sleep(0.1)
        print(f"loading about {name}")
        tmp += [get_pages(url, interval=10)]
    df["pages"] = tmp
    ### 研究者ごとにhtmlを解析し，更新日を取得
    dates = []
    for ix in trange(df.shape[0]):
        line = df.iloc[ix]
        name = line["name"]
        try:
            date = get_update_date(line["pages"])
        except:
            print("error occurred. @", name)
            src = get_pages(line["url"], interval=10)
            date = get_update_date(src)
            df.iloc[ix,3] = src
            print(date, "is extracted from", line["url"])
        dates.append(date)
        
    today = datetime.today().strftime('%Y/%m/%d')
    dates = [date if ":" not in date else today for date in dates ]
    df["updated_date"] = dates
    
    ## データの保存
    # resultsディレクトリが存在しない場合は作成
    results_dir = Path("./results")
    results_dir.mkdir(exist_ok=True)
    
    # 現在の日時からファイル名を作成
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日")
    
    df.to_pickle(f"./results/df_{date_str}.pickle")
    df[['name', 'kana', 'url', 'updated_date']].to_csv(f"./results/ResearchMap_Update_Dates_{date_str}.csv", encoding="utf-8-sig")
    