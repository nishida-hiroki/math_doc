数学の勉強メモです．
とりあえず円分多項式とルベーグ積分の勉強してます


tagsのところに資料があります．

## LaTeX のビルド

Ubuntu 系なら次を入れると `memo/memo.tex` をビルドできます．

```bash
sudo apt-get update
sudo apt-get install -y latexmk texlive-lang-japanese texlive-latex-extra texlive-pictures texlive-plain-generic
```

ビルドはリポジトリ直下で実行します．

```bash
bash scripts/build-memo.sh
```

生成物は `build/` に出力されます．PDF は `build/memo.pdf` です．

`make` が入っていれば `make memo` でも同じです．
