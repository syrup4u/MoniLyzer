sudo pmacctd -f pmacctd.conf | rotatelogs ./data/traffic_%Y%m%d_%H%M.json 60
# sudo pmacctd -f pmacctd.conf