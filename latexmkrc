$latex = 'uplatex %O -interaction=nonstopmode -halt-on-error %S';
$bibtex = 'upbibtex %O %B';
$makeindex = 'mendex %O -U %S';
$dvipdf = 'dvipdfmx %O -o %D %S';
$pdf_mode = 3;
$max_repeat = 5;
$out_dir = 'build';
$clean_full_ext = 'aux bbl bcf blg dvi fdb_latexmk fls idx ilg ind lof log lot nav out run.xml snm toc vrb';
