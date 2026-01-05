# Retrieving update date of Researchmap

Researchmap（日本の研究者情報データベース）から、指定された組織に所属する研究者のページ更新日を取得するツールです。

> Note: Refactoring and README.md creation were performed by Cursor Agent.

## 概要

このプロジェクトは、Researchmapから研究者情報を取得し、各研究者ページの最終更新日をチェックするためのツールです。Seleniumを使用してWebスクレイピングを行います。

## 必要な環境

- Python 3.10以上
- Chromeブラウザ（Seleniumで使用）
- [uv](https://docs.astral.sh/uv/#installation)（パッケージ管理ツール）

## インストール

### 依存関係のインストール

```bash
uv sync
```

これにより、以下のパッケージがインストールされます：
- pandas
- tqdm
- webdriver-manager
- selenium
- beautifulsoup4

## 使い方

### 基本的な使い方

`main.py`を実行することで、指定された組織に所属する研究者の更新日を取得できます。

```bash
uv run main.py --institution_code 6520 --limit 200
```

#### コマンドライン引数

- `--institution_code`: 組織コード（デフォルト: `6520`）
  - 学校ごとに異なるコードが割り当てられています
- `--limit`: 取得する研究者数の上限（デフォルト: `200`）
  - 研究者数がlimitを超えた場合は、limitを超えた分は取得できません
  - 多めに指定することを推奨します

#### 実行例

```bash
# デフォルト設定（組織コード6520、上限200人）で実行
uv run main.py

# 組織コードを指定して実行
uv run main.py --institution_code 6520

# 組織コードと上限を指定して実行
uv run main.py --institution_code 6520 --limit 300
```

#### 出力ファイル

実行が完了すると、`results/`ディレクトリに以下のファイルが生成されます：

- `df_YYYY年MM月DD日.pickle`: 全データを含むpickleファイル
- `ResearchMap_Update_Dates_YYYY年MM月DD日.csv`: 名前、カナ、URL、更新日を含むCSVファイル

### 注意事項

- Seleniumは実際にChromeブラウザを起動するため、処理に時間がかかります（例：60人 × 10秒 = 600秒）。
- 時間に余裕を持って実行してください。
- デフォルトのインターバルでは取得がうまくいかない場合（論文が多すぎてページが重いなど）、例外処理により再度その研究者ページのHTMLをダウンロードして再試行します。
- 更新日の要素が見つからない場合は、現在の日付が設定されます。

### Google Colaboratoryで実行する場合

Google Colaboratoryで実行する場合は、最初に以下のコードセルを実行してChromeとChromeDriverをインストールしてください。最初のバージョンでは動作を確認していましたが、今は非推奨です。ローカル環境でuv runすることをお勧めします。

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

インストールスクリプトの出典：See [Google ColaboratoryでSeleniumを使うための設定方法 | DevelopersIO](https://dev.classmethod.jp/articles/google-colaboratory-use-selenium/)

## 処理の流れ

1. コマンドライン引数で指定された組織コード（institution code）と研究者数の上限（limit）を使用します。
2. その組織に所属する研究者の一覧（名前、カナ、URL）を取得します。
3. 取得した研究者一覧に対して、各研究者のページを取得し、更新日を抽出します（毎回0.1秒のインターバルを設けます）。
4. 更新日は`div`タグの`rm-modified text-right`クラスに表示されているので、これを取得します。
5. 更新日の取得に失敗した場合は、例外処理により再度その研究者ページのHTMLをダウンロードして再試行します。
6. 取得した全てのデータをpickleファイルとCSVファイルに出力します。

## パッケージ管理

このプロジェクトは`uv`を使用してパッケージ管理を行います。

- パッケージの追加: `uv add パッケージ名`
- 依存関係の同期: `uv sync`
- コマンドの実行: `uv run コマンド名`

## ライセンス

MIT License

## 作成者

Riki Murakami (mriki@ichinoseki.ac.jp)
