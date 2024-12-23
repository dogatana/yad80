# yad80 - Yet Another Disassembler for Z80

## はじめに

yad80 はアセンブル可能なアセンブラソースを出力可能なZ80逆アセンブラです。

## インストール

```
pip install yad80
```

## 説明

### 動作モード

yad80 は次の二つの動作モードを持っており、実行時のオプションによって選択します。

- simple 逆アセンブル（以降 __simple__）
    - `--eager` オプションをつけない場合の動作モードです.
    - 指定されたアドレスから、所定の行数もしくは無効命令を検出するまで逆アセンブルします。
- eager 逆アセンブル（以降 __eager__）
    - `--eager` オプションをつけた場合の動作モードです.
    - 開始アドレス
        - 指定されたアドレスから無条件分岐等、実行可能な範囲まで逆アセンブルします。
        - 指定されたアドレス範囲が全て有効な命令として逆アセンブルします。途中で分岐・停止命令があっても有効な Z80 命令である限り逆アセンブルします。
    - 到達可能な範囲を逆アセンブル
        - 逆アセンブル中に検出した分岐アドレスを開始アドレスとして逆アセンブルします。これにより指定アドレス、指定アドレス範囲から到達可能な範囲を逆アセンブルすることとなります。
    - 文字列、データ
        - 文字列として扱う範囲を指定することができ、`DB "ASCII"` のように文字列として出力します。また先頭アドレスに対するラベルを生成します。
        - データとして扱うアドレス範囲を指定することができ、`DB` で出力します。
        - 入力ファイルのアドレス範囲のうち、逆アセンブルで到達したかったデータ領域について `DB` で出力します。
    - ラベル生成
        - 分岐先アドレスに対応するラベルを生成します。
        - 文字列としてしたアドレス範囲の先頭アドレスに対応するラベルを生成します。
        - `($ABCD)` 等、メモリ参照に対するラベルを生成します。
        - ROM 内ルーチンの呼び出し、VRAM、メモリマップトIOへのアクセス等、入力ファイルのアドレス範囲内にないアドレスについて `EQU` 定義を追加します。

### 生成ラベル

- JR, JP, CD はそれぞれ相対ジャンプ、絶対ジャンプ、コールに対応します。同一アドレスに対して複数の分岐があった場合、それら全てを含むラベルを生成します。
- ST は文字列に対応します。
- DT はメモリ参照に対応します。
- EX_ で始まるラベルは入力ファイルのアドレス範囲外のものです

### eager で逆アセンブルを停止する命令

- 無条件 `JP`, 無条件`JR`
- `RET`, `RETI`, `RETN`
- `HALT`

### 入力ファイル

- アドレス情報を持たない機械語ファイル（以降 __bin ファイル__）。ファイル先頭のアドレスが $0000 でない場合、`--offset` オプションでアドレスを指定します。
- アドレス情報を持つ、拡張子 `.mzt` を持つファイル（以降 __mzt ファイル__）

### 標準出力

- 逆アセンブルた結果は標準出力へ出力します。必要に応じてファイルへリダイレクトしてください。
- 出力は z88dk のアセンブラでアセンブル可能となることを確認しています。その他のアセンブラは確認していません。

### 対応している Z80 命令

- Zilog 社の [Z80 CPU User Manual](https://www.zilog.com/docs/z80/um0080.pdf) に定義されているもの - [https://github.com/dogatana/yad80/blob/main/tests/zilog.asm](https://github.com/dogatana/yad80/blob/main/tests/zilog.asm)
- 未公開命令のうち IXH, IXL, IYH, IYL に関する命令 - [https://github.com/dogatana/yad80/blob/main/tests/undocumented_ixy.asm](https://github.com/dogatana/yad80/blob/main/tests/undocumented_ixy.asm)


## 使用方法

### オプション一覧

```
> yad80 -h
usage: yad80 [-h] [--version] [--option OPTION] [--code [RANGE ...]] [--string [RANGE ...]] [--addr [ADDR ...]]
             [--eager] [--debug] [--max-lines N] [--offset OFFSET]
             FILE

positional arguments:
  FILE                  file to disasm

options:
  -h, --help            show this help message and exit
  --version, -v         show program's version number and exit
  --option OPTION       option file
  --code [RANGE ...], -c [RANGE ...]
                        address range(a1-a2) as code. a2 is an inclusive address
  --string [RANGE ...], -s [RANGE ...]
                        address range(a1-a2) as code. a2 is an inclusive address
  --addr [ADDR ...], -a [ADDR ...]
                        address(es) to disasm
  --eager, -e           disasm yeagerly(default false)
  --debug               debug flag
  --max-lines N, -m N   max lines for output(default 32)
  --offset OFFSET, -o OFFSET
                        address offset for binary file
```

### オプション説明

- `--eager`
    - eager モードで逆アセンブルします。
- `--option OPTION`
    - オプションを記述したファイルを指定します。
    - これで指定した内容より、個別に与えたオプションが優先します。
    - ファイルで￥ `;`, `#` 以降は行コメントとなります。
- `--code RANGE` (eager の場合)
    - 逆アセンブルを停止する命令を検出した場合でも指定範囲を全て逆アセンブルします。
- `--string RANGE` (eager の場合)
    - 指定範囲を文字列として DB 定義します。
- `--addr ADDR`
    - 逆アセンブルを開始するアドレスを指定します。
- `--max-lines N` (simple の場合)
    - 逆アセンブルする行数を指定します。指定がない場合は 32行まで逆アセンブルします。
- `--offset OFFSET`
    - bin ファイルの場合、機械語が実際に配置されるアドレスを 16進数 で指定します。

__ADDR__, __OFFSET__
- アドレスは 16進文字列で指定します。<br>指定例: 0-79 はアドレス $0000-$0079 です。

__RANGE（アドレス範囲）__
- 範囲は `[開始アドレス]-[終了アドレス]` の形式で指定します。
- アドレスは 16進文字列で指定します。<br>指定例: 0-79 はアドレス $0000-$0079 です。



### 逆アセンブル方法

`--eager` オプションの指定の有無によって逆アセンブル方法が異なります。

-

| オプション指定 | 逆アセンブル方法 |
| --         | --               |
| なし（not eager）| 指定アドレスから指定行数分、逆アセンブルします。 |
| あり（eager）| 指定アドレス（複数指定可）から全分岐先を辿って逆アセンブルします。入力ファイルの範囲内で辿れなかった個所はデータとして(`DB`)で定義し、出力します。|

次のオペコードを分岐とみなします。

- `JR`
- `JP`
- `DJNZ`
- `CALL`

### 利用可能なオプション

```
usage: yad80 [-h] [--data] [--code [RANGE ...]] [--string [RANGE ...]] [--addr [ADDR ...]] [--eager] [--max-lines N]
             [--offset OFFSET]
             FILE
```

<style>
table:first-child tr td:nth-child(2) {
    color: blue;
    font-family: consolas, monotype
}
</style>
| オプション | 説明 | eager | 非eager |
| --         | --   | :--:  | :--:    |
|  -h, --help          | ヘルプの表示 | - | - |
|  --data, -d          | 未実装       | - | - |
|  --code [RANGE ...],-c [RANGE ...] | コード範囲の指定| - | &#x2713; |
|  --string [RANGE ...], -s [RANGE ...] | 文字列範囲の指定 |  &#x2713; | &#x2713; |
|  --addr [ADDR ...], -a [ADDR ...] | 逆アセンブルの開始アドレスの指定 | &#x2713; | &#x2713; |
|  --eager, -e         | eager モードの逆アセンブルを指定 | &#x2713; | |
|  --max-lines N, -m N | eager モードでない逆アセンブル時、逆アセンブルする行数を指定| | &#x2713; |
|  --offset OFFSET, -o OFFSET | ファイルの先頭が 0 番地でない場合にそのアドレスを指定する | &#x2713; | &#x2713; |

- 範囲は 先頭アドレスを末尾アドレスを `-` で結合して指定します。複数の範囲を指定することができます<br>例）`-c 40-47`
- 開始アドレスが複数指定された場合は eager モードかどうかで次のように動作します。
    - eager あり: 指定されたアドレスを全て分岐先として逆アセンブル
    - eager なし: 最初に指定されたアドレスから逆アセンブル
- 開始アドレスが指定されなかった場合、MZT ファイルではヘッダ内の開始アドレスから、BIN ファイルではファイル先頭のアドレスが指定されたものとして動作します。
-- 〇〇オプションを指定した場合、対象ファイルとの間にオプション終了の区切り `--` を指定してください。<br>例） `python -m yad80 -e -a 41 42 43 -- NEWMONITOR7.ROM`



                        address range(a1-a2) as code. a2 is an inclusive address
                        address range(a1-a2) as code. a2 is an inclusive address

    - `JR`, `JP`, `CALL`

## オプション

## 使用例
