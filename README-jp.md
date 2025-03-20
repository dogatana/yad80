# yad80 - Yet Another Disassembler for Z80

## はじめに

yad80 はアセンブル可能なアセンブラソースを出力する Z80逆アセンブラです。

## インストール

```
pip install yad80
```

## 説明

### 逆アセンブル可能な Z80 命令

- Zilog 社の [Z80 CPU User Manual](https://www.zilog.com/docs/z80/um0080.pdf) に定義されている命令<br>[https://github.com/dogatana/yad80/blob/main/tests/zilog.asm](https://github.com/dogatana/yad80/blob/main/tests/zilog.asm)
- Zilog 未公開命令のうち IXH, IXL, IYH, IYL に関する命令<br>[https://github.com/dogatana/yad80/blob/main/tests/undocumented_ixy.asm](https://github.com/dogatana/yad80/blob/main/tests/undocumented_ixy.asm)

### 入力ファイル

- 拡張子 `.mzt` を持つ機械語ファイル（以降 __mzt ファイル__）
    - アトリビュート（ファイルモード）が $01 のものが対象です。
    - 複数のデータをまとめた mzt ファイルは扱えません。
- アドレス情報を持たない機械語ファイル（以降 __bin ファイル__）。
    - ファイル拡張子は任意です。
    - ファイル先頭のアドレスが $0000 でない場合、`--offset` オプションでそのアドレスを指定します。


### 逆アセンブル結果の出力

- 逆アセンブルの結果は標準出力へ出力します。必要に応じてファイルへリダイレクトしてください。
- 出力は z88dk のアセンブラでアセンブルできることを確認しています。その他のアセンブラは確認していません。

### 動作モード

yad80 は次の二つの動作モードを持っており、実行時のオプションによって選択します。

- simple 逆アセンブル（以降 __simple__）
    - `--eager` オプションをつけない場合の動作モードです.
    - 指定されたアドレスから、所定の行数、ファイル末尾、もしくは無効命令を検出するまで逆アセンブルします。
    - 開始アドレス
        - `--addr` オプションで指定している場合はそのアドレス
        - `--addr` オプションで指定していない場合、bin ファイルはファイルの先頭アドレス、mzt ファイルはヘッダ内の実行開始アドレスです。
- eager 逆アセンブル（以降 __eager__）
    - `--eager` オプションをつけた場合の動作モードです.
    - 開始アドレス
        - simple と同様の開始アドレスです。
        - `--addr` オプションに複数の開始アドレスを指定した場合、その全てを開始アドレスとして処理します。
        - 指定されたアドレスから無条件分岐等、実行可能な範囲まで逆アセンブルします。
    - アドレス範囲指定
        - アドレス範囲を指定可能です。
        - 指定されたアドレス範囲全てを有効命令の列として逆アセンブルします。途中で分岐・停止命令があっても逆アセンブルを継続します。
    - 到達可能な範囲を逆アセンブル
        - 逆アセンブル中に検出した分岐アドレスを開始アドレスとして逆アセンブルします。これにより指定アドレス、指定アドレス範囲から到達可能な全範囲を逆アセンブルすることとなります。
    - データ
        - 入力ファイルのアドレス範囲のうち、逆アセンブルで到達しなかったデータ領域について `DB` で出力します。
    - 文字列
        - 文字列として扱う範囲を指定することができ、`DB "ASCII"` のように文字列として出力します。
        - 先頭アドレスに対するラベルを生成します。
    - ラベル生成
        - 分岐先アドレスに対応するラベルを生成します。
        - 文字列と指定したアドレス範囲の先頭アドレスに対応するラベルを生成します。
        - `($ABCD)` 等、メモリ参照に対するラベルを生成します。
        - `LD HL,$ABCD` 等、直値に対するラベルは生成しません。
        - ROM 内ルーチンの呼び出し、VRAM、メモリマップトIOへのアクセス等、入力ファイルのアドレス範囲内にないアドレスについて `EQU` 定義を追加します。
    - クロスリファレンス
        - 逆アセンブル出力に続けて、各ラベルのクロスリファレンス情報をコメントとして出力します。
    - データ定義領域サマリ
        - クロスリファレンス出力に続けて、DB 定義内容の先頭のアスキー出力をサマリとしてコメント出力します。

### 生成ラベル

- `JR`, `JP`, `CD` はそれぞれ相対ジャンプ、絶対ジャンプ、コールに対応します。同一アドレスに対して複数の分岐があった場合、それら全てを含むラベルを生成します。
- `ST` は文字列に対応します。
- `DT` はメモリ参照に対応します。
- `CO` は --code で指定した領域の先頭アドレスです。
- `AO` は --addr で指定したアドレスです。
- `EX` で始まるラベルは入力ファイルのアドレス範囲外のアドレスです。
- 出力例

```
EX_DT_E000      EQU   $e000
                ORG   $0000
                JP      JP_004A
CD_0003:        JP      JP_07E6
CDJP_0006:      JP      JP_090E
```

- 自己書換コードの場合、ラベルは EQU 定義しますが、命令の先頭アドレスとしては出力されません（できません）。<br>ただし EQU 定義に `; within CODE` コメントを追加します。
```
DT_460C         EQU   $460c ; within CODE

                LD      (DT_460C),A
                LD      A,(IX+$02)
                BIT     0,C
                JR      Z,JR_460B
                DEC     A

JR_460B:        ADD     A,$00
                CALL    CD_45F2
```


### eager で分岐とみなす命令

- `JP`
- `JR`
- `DJNZ`
- `CALL`

### eager で逆アセンブルを停止する命令

- 無条件 `JP`
- 無条件`JR`
- `RET`, `RETI`, `RETN`
- `HALT`


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
                        address range(a1-a2) as string. a2 is an inclusive address
  --addr [ADDR ...], -a [ADDR ...]
                        address to disasm
  --eager, -e           disasm eagerly(default false)
  --debug               debug flag(dev use)
  --max-lines N, -m N   max lines to output(default 32)
  --offset OFFSET, -o OFFSET
                        address offset for binary file
```

### オプション説明（自明なもの以外）

- `--eager`
    - eager を指定します
- `--option OPTION` (simple, eager)
    - オプションを記述したファイルを指定します。
    - この指定内容より、個別に与えたオプションが優先します。
    - ファイルで `;`, `#` 以降は行コメントとなります。

```
# OPTION example
-e       # eager
-c 0-79  # JP xxxx 

# string defs
-s 131-137 ; FOUND
-s 138-140 ; LOADING
-s 141-158 ; ** MZ.MONITOR....

; $0131-$0158, [$ 28] FOUND .LOADING . ** MZ.MONITOR VER4.4 **.
; 
; ST_0131:        DB    "FOUND ",$0D  
; ST_0138:        DB    "LOADING ",$0D
; ST_0141:        DB    "** MZ",$90,"MONITOR VER4.4 **",$0D
```
- `--code RANGE` (eager)
    - 逆アセンブルを停止する命令を含むかどうかに関わらず、指定範囲全てを逆アセンブルします。
- `--string RANGE` (eager)
    - 指定範囲を文字列として DB 定義します。
- `--addr ADDR` (simple, eager)
    - 逆アセンブルを開始するアドレスを指定します。
- `--max-lines N` (simple)
    - 逆アセンブルする行数を指定します。指定がない場合は 32行まで逆アセンブルします。
- `--offset OFFSET` (simple, eager)
    - bin ファイルの場合、機械語が実際に配置されるアドレスを 16進数 で指定します。

__ADDR__, __OFFSET__
- アドレスは 16進文字列で指定します。$, 0x, H 等は不要です。

__RANGE（アドレス範囲）__

- 範囲は `[開始アドレス]-[終了アドレス]` の形式で、途中に __空白を入れずに__ 指定します。
- 終了アドレスはアドレス範囲に含みます。
- 開始アドレス、終了アドレスは 16進文字列で指定します。
- 指定例: `0-79` これは $0000-$0079 です。

__FILE__

- 複数の値を指定可能なオプションと FILE の前には `--`（オプション指定終了）を入れてください。


## 更新履歴

- v0.2.1 Bug Fix: 先頭から開始アドレスまで DB を生成する際に1バイト分不足していたのを修正
- v0.2.0 --addr, --code のラベル生成追加
- v0.1.6 Bug fix: bin ファイルで offset を指定しても逆アセンブル開始アドレスに反映されない不具合を修正
- v0.1.5 Bug fix: 格納開始アドレスと実行開始アドレスが異なる場合、DB が作成されない不具合を修正
- v0.1.4 Bug fix: `--addr` option
- v0.1.3 `EQU` の後に空白挿入
- v0.1.2 Bug fix: `--offset` option
- v0.1.0 公開

End of Document