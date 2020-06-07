mkdir website; cd website;
python3 ../request.py
wget \
 --load-cookies cookie.tmp \
 --keep-session-cookies \
 --save-cookies cookie.tmp2 \
 --no-clobber \
 --page-requisites \
 --force-directories \
 --no-host-directories \
 --convert-links \
 --recursive \
 --reject-regex 'logout|home|polls|imghome' \
 --level=2 \
 https://yearbook.sarc-iitb.org/profile/
