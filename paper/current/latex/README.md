# 中文论文 LaTeX 整合稿

[位置索引](LOCATIONS.md) 列出全部 80 个稳定标签、中文标题、编号及当前 PDF 页码，可直接跳转到对应页。

`main.tex` 包含摘要、正文、附录 A—D 和统一参考文献调用。`main.pdf` 为同一源文件编译的阅读稿。图和表使用交叉引用；参考文献已采用 bibkey，编号按当前首次引用顺序生成。引文暂以红色上标显示，便于作者校阅。

## 文件

- `main.tex`：完整论文正文和附录。
- `references.bib`：全文实际引用的 33 项文献；26 项采用已取得的官方导出，7 项保留官方规范或法规的固定版本信息；第 11 条按出版社页面补全缺失字段。
- `main.bbl`：本次编译生成的参考文献排版内容。
- `figures/`：8 张图的可编辑 SVG 和嵌入字体的 PDF；图 2 已与自动链接及异常处理流程一致。
- `sn-jnl.cls`、`sn-mathphys-num.bst`：Springer Nature 官方模板文件，原样保留。
- `sosym-review-num.bst`：由官方数字引用样式派生，省略缺失的可选出版地和重复 DOI 链接，并保留导出题名的大小写；未补写文献信息。

## 编译

在本目录执行：

```sh
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

也可以使用 `latexmk -xelatex main.tex`，或在 Overleaf 中选择 XeLaTeX。中文采用 TeX 发行版中的 Fandol 字体，西文采用 TeX Gyre 与 Latin Modern 字体；无需作者电脑上的私有字体。图中的中文已嵌入 PDF。

本次也使用 Tectonic 0.17.0 编译验证：

```sh
tectonic --untrusted --keep-logs --keep-intermediates main.tex
```

类选项中的 `pdflatex` 用于选择官方模板的 PDF 链接兼容分支；本中文稿的实际编译引擎为 XeLaTeX 或 Tectonic，不使用 pdfLaTeX。模板、样式和图应与源文件一起保留。

## 论文与证据

[逐项对应表](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/PAPER_ARTIFACT_CROSSWALK.md)将正文、附录、原始材料及审稿意见关联起来；[审稿回应矩阵](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/paper/REVIEW_RESPONSE_MATRIX.md)保留 31 项意见。文件中的 `\label` 和 `\ref` 用于维持这些位置的对应，编译后的位置索引随材料提供。

作者顺序、机构和已提供的联系方式沿用原始论文，未补写原稿没有给出的邮箱。此稿保持中文，供作者审阅内容和修订；不将中文预览视为已完成英文投稿。

格式依据：[SoSyM 投稿说明](https://link.springer.com/journal/10270/submission-guidelines)。官方模板来自该说明所链接的 [Springer Nature LaTeX author support](https://www.springernature.com/gp/authors/campaigns/latex-author-support)，使用 `iicol` 双栏选项。模板中的字体与标题本地化仅在 `main.tex` 中配置。

本压缩包包含编译论文所需的全部源文件、模板与图。ICM、提示、生成制品和实验分析位于完整审稿复现包；完整包中的相对路径可离线使用。

## 本次参考文献修订

[引用核对](引用核对/README.md)提供官方导出来源、原始 BibTeX、字段补全依据和当前引用位置；本轮修订五处文字及两项书目信息；[红色修改对照](引用核对/引文修改对照.html)供逐句审阅。
