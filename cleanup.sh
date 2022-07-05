for o in $(ls obs/); do let x=$(find obs/$o -name '*.png' | wc -l); if (($x==0)); then echo $o; rm -rf obs/$o; fi; echo -----; done
