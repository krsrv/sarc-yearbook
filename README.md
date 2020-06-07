# Offline SARC Yearbook
Download the SARC Yearbook to your computer
There are three levels of hierarchy downloaded:
* Your profile page
* The pages of people who wrote on your page
* The pages of people who wrote on the pages of people who wrote on your page

So for example, if I am A and I wrote for B, B wrote for C, C wrote for D (A, B, C, D all distinct) then pages for A, B, C will be downloaded.

## Requirements
    requests==2.18.4

## Usage
Open `request.py` and enter your LDAP-ID and password in the fields `httpd_username` and `httpd_password` respectively
Then simply execute this in your terminal:
    
    ./run.sh


It will take quite some time to download the pages - I got around 450 folders finally in around 20 minutes. The actual download size will be lesser than the eventual size of the folder `website` because compression methods are used to send over files.
Once the files are downloaded, i.e., `run.sh` has executed (or even while the files are downloading), run a simple server with the folder `website` as the root. For instance, if I use the `python3` module `http.server`:
    
    python3 -m http.server 9000

In your browser, open `localhost:9000/profile`. For `python2` the corresponding module will be `SimpleHTTPServer`.

## Debugging
### 500: Internal Server Error
Most likely the login credentials supplied are incorrect. Check the `request.py` file for the fields `httpd_username` and `httpd_password` and see whether they are set appropriately.

### KeyError: 'location'
Most likely the login credentials supplied are incorrect. Check the `request.py` file for the fields `httpd_username` and `httpd_password` and see whether they are set appropriately.
